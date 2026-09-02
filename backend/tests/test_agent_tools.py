"""NoteAssistant 工具注册与参数校验测试。

覆盖：
- 所有工具 schema 均有对应 handler 与子 Agent 映射
- 子 Agent 映射指向已注册的 SUB_AGENTS
- 各工具入参校验（空参数返回 error，不触达外部服务）
- 对话标题生成（截断 / 空输入）
"""

import pytest

from app.services.agent.note_assistant import (
    NOTE_ASSISTANT_TOOLS,
    SUB_AGENTS,
    TOOL_HANDLERS,
    TOOL_TO_SUB_AGENT,
    _make_conversation_title,
    _tool_create_note,
    _tool_generate_note,
    _tool_get_note_content,
    _tool_summarize_note,
    _tool_translate_note,
)


def test_all_tool_schemas_have_handlers_and_mapping():
    tool_names = {t["function"]["name"] for t in NOTE_ASSISTANT_TOOLS}
    assert tool_names == set(TOOL_HANDLERS.keys())
    assert tool_names == set(TOOL_TO_SUB_AGENT.keys())


def test_sub_agent_mapping_refers_to_registered_agents():
    for key in TOOL_TO_SUB_AGENT.values():
        if key is not None:
            assert key in SUB_AGENTS


class TestToolValidation:
    @pytest.mark.asyncio
    async def test_get_note_content_rejects_non_positive_id(self):
        result = await _tool_get_note_content(None, 1, {"note_id": 0}, None)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_summarize_rejects_empty_content(self):
        result = await _tool_summarize_note(None, 1, {"content": "   "}, None)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_generate_rejects_empty_topic(self):
        result = await _tool_generate_note(None, 1, {"topic": ""}, None)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_translate_requires_target_lang(self):
        result = await _tool_translate_note(None, 1, {"content": "hello", "target_lang": ""}, None)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_create_note_requires_title_and_content(self):
        result = await _tool_create_note(None, 1, {"title": "", "content": ""}, None)
        assert "error" in result


class TestConversationTitle:
    def test_truncates_long_message(self):
        title = _make_conversation_title("x" * 100)
        assert len(title) == 50 + 1
        assert title.endswith("…")

    def test_short_message_kept(self):
        assert _make_conversation_title("你好，帮我总结") == "你好，帮我总结"

    def test_empty_message_default(self):
        assert _make_conversation_title("") == "新对话"
        assert _make_conversation_title("   ") == "新对话"
