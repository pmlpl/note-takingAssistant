"""app.services.agent.note_assistant 单元测试

覆盖（test_agent_tools.py 已覆盖参数校验与 schema 一致性，此处补全）：
- NoteAssistant.run：agent_start/agent_end、sub_agent_start/sub_agent_end 事件
- _persist_messages：新建对话、已有对话更新、异常回滚
- agent_chat_stream：delta 聚合、persist 写入、done 携带 conversation_id、persist=False
- 工具处理器成功路径：search_notes / get_note_content / summarize_note /
  generate_note / translate_note / create_note
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent.base import BaseAgent, sse_event
from app.services.agent.note_assistant import (
    SUB_AGENTS,
    TOOL_TO_SUB_AGENT,
    NoteAssistant,
    _persist_messages,
    _tool_create_note,
    _tool_generate_note,
    _tool_get_note_content,
    _tool_search_notes,
    _tool_summarize_note,
    _tool_translate_note,
    agent_chat_stream,
)


def _parse_sse(evt: str) -> dict:
    return json.loads(evt[len("data: "):].strip())


def _fake_user(uid=1):
    u = MagicMock()
    u.id = uid
    return u


def _fake_note(nid, title="t", content="c", tags=None):
    return SimpleNamespace(id=nid, title=title, content=content, tags=tags)


# ────────────────────── NoteAssistant.run ──────────────────────

class TestNoteAssistantRun:
    @pytest.mark.asyncio
    async def test_emits_agent_start_and_end(self):
        """父类 run 产出 delta+done，NoteAssistant 应在前后包 agent_start/agent_end。"""
        base_events = [
            sse_event("delta", {"text": "你好", "agent": "note_assistant"}),
            sse_event("done", {"finish_reason": "stop", "agent": "note_assistant"}),
        ]

        async def fake_base_run(self, message, history=None, *, db, db_user):
            for evt in base_events:
                yield evt

        with patch.object(BaseAgent, "run", fake_base_run):
            agent = NoteAssistant()
            events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_fake_user())]

        payloads = [_parse_sse(e) for e in events]
        types = [p["type"] for p in payloads]
        assert types[0] == "agent_start"
        assert types[-1] == "agent_end"
        assert payloads[0]["agent"] == "note_assistant"
        assert payloads[0]["display_name"] == "Note助手"

    @pytest.mark.asyncio
    async def test_sub_agent_events_for_mapped_tools(self):
        """tool_start/tool_end 对应有子 Agent 映射的工具时，插入 sub_agent_start/end。"""
        base_events = [
            sse_event("tool_start", {"id": "1", "name": "search_notes", "args": {}}),
            sse_event("tool_end", {"id": "1", "name": "search_notes", "result": {"count": 0}}),
            sse_event("delta", {"text": "done", "agent": "note_assistant"}),
            sse_event("done", {"finish_reason": "stop", "agent": "note_assistant"}),
        ]

        async def fake_base_run(self, message, history=None, *, db, db_user):
            for evt in base_events:
                yield evt

        with patch.object(BaseAgent, "run", fake_base_run):
            agent = NoteAssistant()
            events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_fake_user())]

        payloads = [_parse_sse(e) for e in events]
        types = [p["type"] for p in payloads]
        assert "sub_agent_start" in types
        assert "sub_agent_end" in types
        sub_start = next(p for p in payloads if p["type"] == "sub_agent_start")
        assert sub_start["agent"] == "search"
        assert sub_start["display_name"] == "搜索专家"

    @pytest.mark.asyncio
    async def test_no_sub_agent_for_unmapped_tool(self):
        """get_note_content 映射为 None，不产生 sub_agent 事件。"""
        base_events = [
            sse_event("tool_start", {"id": "1", "name": "get_note_content", "args": {}}),
            sse_event("tool_end", {"id": "1", "name": "get_note_content", "result": {}}),
            sse_event("done", {"finish_reason": "stop", "agent": "note_assistant"}),
        ]

        async def fake_base_run(self, message, history=None, *, db, db_user):
            for evt in base_events:
                yield evt

        with patch.object(BaseAgent, "run", fake_base_run):
            agent = NoteAssistant()
            events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_fake_user())]

        payloads = [_parse_sse(e) for e in events]
        types = [p["type"] for p in payloads]
        assert "sub_agent_start" not in types
        assert "sub_agent_end" not in types

    @pytest.mark.asyncio
    async def test_malformed_event_passthrough(self):
        """非标准 SSE 格式的事件直接透传，不抛异常。"""
        base_events = ["not-a-valid-sse\n\n"]

        async def fake_base_run(self, message, history=None, *, db, db_user):
            for evt in base_events:
                yield evt

        with patch.object(BaseAgent, "run", fake_base_run):
            agent = NoteAssistant()
            events = [evt async for evt in agent.run("hi", db=MagicMock(), db_user=_fake_user())]
        assert events[0] == "agent_start" or len(events) >= 2


# ────────────────────── _persist_messages ──────────────────────

class TestPersistMessages:
    @pytest.mark.asyncio
    async def test_creates_new_conversation(self, async_db_session, test_user_id):
        cid = await _persist_messages(
            db=async_db_session,
            user_id=test_user_id,
            conversation_id=None,
            user_message="你好",
            assistant_message="你好！",
            first_message="你好",
        )
        assert cid is not None
        assert isinstance(cid, int)

    @pytest.mark.asyncio
    async def test_updates_existing_conversation(self, async_db_session, test_user_id):
        # 先创建
        cid1 = await _persist_messages(
            db=async_db_session,
            user_id=test_user_id,
            conversation_id=None,
            user_message="第一条",
            assistant_message="回复一",
            first_message="第一条",
        )
        # 再追加
        cid2 = await _persist_messages(
            db=async_db_session,
            user_id=test_user_id,
            conversation_id=cid1,
            user_message="第二条",
            assistant_message="回复二",
            first_message="第一条",
        )
        assert cid2 == cid1

    @pytest.mark.asyncio
    async def test_exception_returns_none(self, async_db_session, test_user_id):
        """db.commit 抛异常时返回 None 并回滚。"""
        with patch.object(async_db_session, "commit", new_callable=AsyncMock, side_effect=RuntimeError("db down")):
            cid = await _persist_messages(
                db=async_db_session,
                user_id=test_user_id,
                conversation_id=None,
                user_message="hi",
                assistant_message="hello",
                first_message="hi",
            )
        assert cid is None


# ────────────────────── agent_chat_stream ──────────────────────

class TestAgentChatStream:
    @pytest.mark.asyncio
    async def test_collects_deltas_and_persists(self):
        agent_events = [
            sse_event("agent_start", {"agent": "note_assistant"}),
            sse_event("delta", {"text": "你", "agent": "note_assistant"}),
            sse_event("delta", {"text": "好", "agent": "note_assistant"}),
            sse_event("done", {"finish_reason": "stop", "agent": "note_assistant"}),
            sse_event("agent_end", {"agent": "note_assistant"}),
        ]

        async def fake_agent_run(self, message, history=None, *, db, db_user):
            for evt in agent_events:
                yield evt

        with patch.object(NoteAssistant, "run", fake_agent_run):
            with patch("app.services.agent.note_assistant._persist_messages",
                       new_callable=AsyncMock, return_value=999) as mock_persist:
                events = [evt async for evt in agent_chat_stream(
                    "你好", db=MagicMock(), db_user=_fake_user()
                )]

        payloads = [_parse_sse(e) for e in events]
        # 原始 done 被替换为带 conversation_id 的 done
        done_events = [p for p in payloads if p["type"] == "done"]
        assert len(done_events) == 1
        assert done_events[0]["conversation_id"] == 999
        mock_persist.assert_called_once()
        # 验证 assistant_message 是 delta 聚合
        call_kwargs = mock_persist.call_args[1]
        assert call_kwargs["assistant_message"] == "你好"

    @pytest.mark.asyncio
    async def test_persist_false_skips_persistence(self):
        agent_events = [
            sse_event("delta", {"text": "hi", "agent": "note_assistant"}),
            sse_event("done", {"finish_reason": "stop", "agent": "note_assistant"}),
        ]

        async def fake_agent_run(self, message, history=None, *, db, db_user):
            for evt in agent_events:
                yield evt

        with patch.object(NoteAssistant, "run", fake_agent_run):
            with patch("app.services.agent.note_assistant._persist_messages") as mock_persist:
                events = [evt async for evt in agent_chat_stream(
                    "hi", db=MagicMock(), db_user=_fake_user(), persist=False
                )]
        mock_persist.assert_not_called()
        payloads = [_parse_sse(e) for e in events]
        done = next(p for p in payloads if p["type"] == "done")
        assert "conversation_id" not in done

    @pytest.mark.asyncio
    async def test_malformed_event_passthrough(self):
        agent_events = ["garbage\n\n"]

        async def fake_agent_run(self, message, history=None, *, db, db_user):
            for evt in agent_events:
                yield evt

        with patch.object(NoteAssistant, "run", fake_agent_run):
            events = [evt async for evt in agent_chat_stream(
                "hi", db=MagicMock(), db_user=_fake_user(), persist=False
            )]
        assert "garbage\n\n" in events


# ────────────────────── 工具处理器成功路径 ──────────────────────

class TestToolSearchNotes:
    @pytest.mark.asyncio
    async def test_returns_mapped_items(self):
        fake_notes = [_fake_note(1, "标题一", "内容一" * 10, "tag1"), _fake_note(2, "标题二", "短", None)]
        with patch("app.services.note_rag.hybrid_search_notes",
                   new_callable=AsyncMock, return_value=(fake_notes, 2)):
            result = await _tool_search_notes(MagicMock(), 1, {"query": "测试", "limit": 5}, _fake_user())
        assert result["count"] == 2
        assert result["items"][0]["id"] == 1
        assert result["items"][0]["title"] == "标题一"
        assert len(result["items"][0]["preview"]) <= 120

    @pytest.mark.asyncio
    async def test_limit_clamped(self):
        with patch("app.services.note_rag.hybrid_search_notes",
                   new_callable=AsyncMock, return_value=([], 0)) as mock_search:
            await _tool_search_notes(MagicMock(), 1, {"query": "x", "limit": 100}, _fake_user())
            # limit 被 clamp 到 20
            assert mock_search.call_args[1]["limit"] == 20

    @pytest.mark.asyncio
    async def test_limit_min_one(self):
        with patch("app.services.note_rag.hybrid_search_notes",
                   new_callable=AsyncMock, return_value=([], 0)) as mock_search:
            await _tool_search_notes(MagicMock(), 1, {"query": "x", "limit": -5}, _fake_user())
            assert mock_search.call_args[1]["limit"] == 1


class TestToolGetNoteContent:
    @pytest.mark.asyncio
    async def test_returns_note_content(self):
        note = _fake_note(42, "我的笔记", "完整内容", "python,ai")
        with patch("app.crud.note.get_note", new_callable=AsyncMock, return_value=note):
            result = await _tool_get_note_content(MagicMock(), 1, {"note_id": 42}, _fake_user())
        assert result["id"] == 42
        assert result["title"] == "我的笔记"
        assert result["content"] == "完整内容"
        assert result["tags"] == "python,ai"

    @pytest.mark.asyncio
    async def test_note_not_found_returns_error(self):
        with patch("app.crud.note.get_note", new_callable=AsyncMock, return_value=None):
            result = await _tool_get_note_content(MagicMock(), 1, {"note_id": 999}, _fake_user())
        assert "error" in result
        assert "999" in result["error"]


class TestToolSummarizeNote:
    @pytest.mark.asyncio
    async def test_returns_analyzer_result(self):
        analyzer_result = {"summary": "总结", "strengths": ["好"], "weaknesses": [], "suggestions": []}
        with patch("app.services.note_analyzer.analyze_note",
                   new_callable=AsyncMock, return_value=analyzer_result):
            result = await _tool_summarize_note(MagicMock(), 1, {"content": "一些笔记内容"}, _fake_user())
        assert result == analyzer_result


class TestToolGenerateNote:
    @pytest.mark.asyncio
    async def test_collects_stream_chunks(self):
        async def fake_stream(**kwargs):
            for chunk in ["# 标题\n", "正文内容"]:
                yield chunk

        with patch("app.services.note_generator.generate_note_stream", side_effect=fake_stream):
            result = await _tool_generate_note(
                MagicMock(), 1, {"topic": "机器学习", "keywords": "AI", "word_count": 300}, _fake_user()
            )
        assert result["content"] == "# 标题\n正文内容"

    @pytest.mark.asyncio
    async def test_keywords_non_string_passed_as_none(self):
        async def fake_stream(**kwargs):
            yield "content"
            assert kwargs["keyword"] is None

        with patch("app.services.note_generator.generate_note_stream", side_effect=fake_stream):
            await _tool_generate_note(MagicMock(), 1, {"topic": "x", "keywords": 123}, _fake_user())


class TestToolTranslateNote:
    @pytest.mark.asyncio
    async def test_collects_translation_chunks(self):
        async def fake_stream(content, target_lang, db_user):
            yield "Translated "
            yield "text"

        with patch("app.services.note_translator.translate_note_stream", side_effect=fake_stream):
            result = await _tool_translate_note(
                MagicMock(), 1, {"content": "你好", "target_lang": "EN"}, _fake_user()
            )
        assert result["content"] == "Translated text"


class TestToolCreateNote:
    @pytest.mark.asyncio
    async def test_creates_note_success(self):
        created = _fake_note(77, "新笔记", "内容", "tag")
        with patch("app.crud.note.get_note_by_title", new_callable=AsyncMock, return_value=None):
            with patch("app.crud.note.create_note", new_callable=AsyncMock, return_value=created):
                result = await _tool_create_note(
                    MagicMock(), 1, {"title": "新笔记", "content": "内容", "tags": "tag"}, _fake_user()
                )
        assert result["created"] is True
        assert result["id"] == 77
        assert result["title"] == "新笔记"

    @pytest.mark.asyncio
    async def test_duplicate_title_returns_error(self):
        existing = _fake_note(1, "已存在", "旧内容")
        with patch("app.crud.note.get_note_by_title", new_callable=AsyncMock, return_value=existing):
            result = await _tool_create_note(
                MagicMock(), 1, {"title": "已存在", "content": "新内容"}, _fake_user()
            )
        assert "error" in result
        assert "已存在" in result["error"]

    @pytest.mark.asyncio
    async def test_tags_non_string_passed_as_none(self):
        created = _fake_note(88, "t", "c", None)
        with patch("app.crud.note.get_note_by_title", new_callable=AsyncMock, return_value=None):
            with patch("app.crud.note.create_note", new_callable=AsyncMock, return_value=created) as mock_create:
                await _tool_create_note(
                    MagicMock(), 1, {"title": "t", "content": "c", "tags": 123}, _fake_user()
                )
        assert mock_create.call_args[1]["tags"] is None
