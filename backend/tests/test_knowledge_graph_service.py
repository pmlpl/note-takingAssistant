"""app.services.knowledge_graph_service 单元测试

覆盖：
- _extract_concepts_with_llm：成功解析、空内容、LLM 异常降级关键词、各种格式
- build_knowledge_graph：空笔记、有笔记+概念、相似度边、TF-IDF 兜底
- save_kg_to_db / get_kg_from_db：持久化与回读
- update_kg_status / get_kg_status：状态管理
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.kg import KGEdge, KGNode
from app.models.note import NoteDB
from app.services.knowledge_graph_service import (
    MAX_CONCEPTS_PER_NOTE,
    SIMILARITY_THRESHOLD,
    _extract_concepts_with_llm,
    build_knowledge_graph,
    get_kg_from_db,
    get_kg_status,
    save_kg_to_db,
    update_kg_status,
)


def _fake_user(uid=1):
    u = MagicMock()
    u.id = uid
    return u


def _make_llm_response(content: str):
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content=content))]
    return mock_resp


def _fake_note(nid, title="t", content="c", tags=None, is_favorite=1, created_at=None, updated_at=None):
    return NoteDB(
        id=nid,
        user_id=1,
        title=title,
        content=content,
        tags=tags,
        is_favorite=is_favorite,
        created_at=created_at,
        updated_at=updated_at,
    )


# ────────────────────── _extract_concepts_with_llm ──────────────────────

class TestExtractConceptsWithLLM:
    @pytest.mark.asyncio
    async def test_success_with_colon_format(self):
        content = "机器学习:0.9\n深度学习:0.8\n神经网络:0.7"
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=_make_llm_response(content))

        with patch("app.services.knowledge_graph_service.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            note = _fake_note(1, title="AI", content="机器学习和深度学习的关系")
            concepts = await _extract_concepts_with_llm(note, _fake_user())

        assert len(concepts) == 3
        assert concepts[0][0] == "机器学习"
        assert concepts[0][1] == 0.9

    @pytest.mark.asyncio
    async def test_success_with_numbered_lines(self):
        content = "1. 机器学习:0.9\n2. 深度学习:0.8\n- 神经网络:0.7"
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=_make_llm_response(content))

        with patch("app.services.knowledge_graph_service.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            note = _fake_note(1, content="some content")
            concepts = await _extract_concepts_with_llm(note, _fake_user())

        assert len(concepts) == 3
        assert concepts[0][0] == "机器学习"

    @pytest.mark.asyncio
    async def test_plain_name_without_weight_defaults_05(self):
        content = "机器学习\n深度学习"
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=_make_llm_response(content))

        with patch("app.services.knowledge_graph_service.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            note = _fake_note(1, content="some content")
            concepts = await _extract_concepts_with_llm(note, _fake_user())

        assert concepts[0][1] == 0.5

    @pytest.mark.asyncio
    async def test_invalid_weight_defaults_05(self):
        content = "机器学习:not-a-number"
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=_make_llm_response(content))

        with patch("app.services.knowledge_graph_service.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            note = _fake_note(1, content="some content")
            concepts = await _extract_concepts_with_llm(note, _fake_user())

        assert concepts[0][1] == 0.5

    @pytest.mark.asyncio
    async def test_weight_clamped_to_range(self):
        content = "概念A:5.0\n概念B:-1.0"
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=_make_llm_response(content))

        with patch("app.services.knowledge_graph_service.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            note = _fake_note(1, content="some content")
            concepts = await _extract_concepts_with_llm(note, _fake_user())

        assert concepts[0][1] == 1.0  # clamped from 5.0
        assert concepts[1][1] == 0.1  # clamped from -1.0

    @pytest.mark.asyncio
    async def test_name_too_short_or_long_skipped(self):
        content = "a:0.5\n这个概念名称实在是太长了超过二十个字符了吧:0.5\n有效概念:0.8"
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=_make_llm_response(content))

        with patch("app.services.knowledge_graph_service.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            note = _fake_note(1, content="some content")
            concepts = await _extract_concepts_with_llm(note, _fake_user())

        assert len(concepts) == 1
        assert concepts[0][0] == "有效概念"

    @pytest.mark.asyncio
    async def test_limits_to_max_concepts(self):
        lines = [f"概念{i}:0.{i}" for i in range(1, 15)]
        content = "\n".join(lines)
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=_make_llm_response(content))

        with patch("app.services.knowledge_graph_service.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            note = _fake_note(1, content="some content")
            concepts = await _extract_concepts_with_llm(note, _fake_user())

        assert len(concepts) == MAX_CONCEPTS_PER_NOTE

    @pytest.mark.asyncio
    async def test_empty_content_returns_empty(self):
        mock_client = MagicMock()
        with patch("app.services.knowledge_graph_service.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            note = _fake_note(1, content="")
            concepts = await _extract_concepts_with_llm(note, _fake_user())
        assert concepts == []

    @pytest.mark.asyncio
    async def test_none_content_returns_empty(self):
        mock_client = MagicMock()
        with patch("app.services.knowledge_graph_service.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            note = _fake_note(1, content=None)
            concepts = await _extract_concepts_with_llm(note, _fake_user())
        assert concepts == []

    @pytest.mark.asyncio
    async def test_llm_exception_falls_back_to_keywords(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("API down"))

        with patch("app.services.knowledge_graph_service.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            note = _fake_note(1, title="机器学习", content="机器学习 深度学习 算法 机器学习")
            concepts = await _extract_concepts_with_llm(note, _fake_user())

        assert len(concepts) > 0
        # 降级使用关键词，"机器学习" 出现频率最高
        assert concepts[0][0] == "机器学习"

    @pytest.mark.asyncio
    async def test_llm_exception_empty_note_returns_empty(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("API down"))

        with patch("app.services.knowledge_graph_service.openai_client_and_model_for_user",
                   return_value=(mock_client, "test-model")):
            note = _fake_note(1, title="", content="")
            concepts = await _extract_concepts_with_llm(note, _fake_user())
        assert concepts == []


# ────────────────────── build_knowledge_graph ──────────────────────

class TestBuildKnowledgeGraph:
    @pytest.mark.asyncio
    async def test_empty_notes_returns_empty(self, async_db_session, test_user_id):
        nodes, edges, stats = await build_knowledge_graph(async_db_session, test_user_id, _fake_user(test_user_id))
        assert nodes == []
        assert edges == []
        assert stats["note_count"] == 0

    @pytest.mark.asyncio
    async def test_builds_graph_with_notes_and_concepts(self, async_db_session, test_user_id):
        # 创建两篇收藏笔记，共享概念
        note1 = NoteDB(user_id=test_user_id, title="机器学习基础",
                       content="机器学习 深度学习 算法 模型训练", is_favorite=1)
        note2 = NoteDB(user_id=test_user_id, title="深度学习进阶",
                       content="深度学习 神经网络 反向传播 梯度下降", is_favorite=1)
        async_db_session.add_all([note1, note2])
        await async_db_session.flush()

        # mock LLM 概念提取
        async def fake_extract(note, db_user):
            if "机器学习" in note.title:
                return [("机器学习", 0.9), ("深度学习", 0.8)]
            return [("深度学习", 0.9), ("神经网络", 0.7)]

        with patch("app.services.knowledge_graph_service._extract_concepts_with_llm",
                   side_effect=fake_extract):
            nodes, edges, stats = await build_knowledge_graph(
                async_db_session, test_user_id, _fake_user(test_user_id)
            )

        assert stats["note_count"] == 2
        # 深度学习出现在两篇笔记中 → 频繁概念
        concept_labels = [n.label for n in nodes if n.type == "concept"]
        assert "深度学习" in concept_labels
        # 机器学习只在一篇 → 不满足 MIN_CONCEPT_NOTE_FREQ=2
        assert "机器学习" not in concept_labels
        assert len(nodes) >= 2  # at least 2 note nodes

    @pytest.mark.asyncio
    async def test_tfidf_fallback_when_no_concepts(self, async_db_session, test_user_id):
        note = NoteDB(user_id=test_user_id, title="Python编程",
                      content="python 函数 类 模块 包 异常处理", is_favorite=1)
        async_db_session.add(note)
        await async_db_session.flush()

        # LLM 返回空概念 → 走 TF-IDF 兜底
        async def fake_extract(note, db_user):
            return []

        with patch("app.services.knowledge_graph_service._extract_concepts_with_llm",
                   side_effect=fake_extract):
            nodes, edges, stats = await build_knowledge_graph(
                async_db_session, test_user_id, _fake_user(test_user_id)
            )

        assert stats["note_count"] == 1
        # 单篇笔记的概念不满足频繁阈值，concept_count=0
        assert stats["concept_count"] == 0

    @pytest.mark.asyncio
    async def test_similarity_edges_between_notes(self, async_db_session, test_user_id):
        # 两篇高度相似的笔记
        content = "机器学习 深度学习 神经网络 算法 模型 训练 数据 特征" * 5
        note1 = NoteDB(user_id=test_user_id, title="笔记A", content=content, is_favorite=1)
        note2 = NoteDB(user_id=test_user_id, title="笔记B", content=content + " 额外词", is_favorite=1)
        async_db_session.add_all([note1, note2])
        await async_db_session.flush()

        async def fake_extract(note, db_user):
            return []

        with patch("app.services.knowledge_graph_service._extract_concepts_with_llm",
                   side_effect=fake_extract):
            nodes, edges, stats = await build_knowledge_graph(
                async_db_session, test_user_id, _fake_user(test_user_id)
            )

        note_edges = [e for e in edges if e.type == "note-note"]
        assert len(note_edges) >= 1
        assert stats["note_edges"] >= 1

    @pytest.mark.asyncio
    async def test_non_favorite_notes_excluded(self, async_db_session, test_user_id):
        note1 = NoteDB(user_id=test_user_id, title="收藏笔记", content="机器学习 深度学习", is_favorite=1)
        note2 = NoteDB(user_id=test_user_id, title="普通笔记", content="机器学习 深度学习", is_favorite=0)
        async_db_session.add_all([note1, note2])
        await async_db_session.flush()

        async def fake_extract(note, db_user):
            return []

        with patch("app.services.knowledge_graph_service._extract_concepts_with_llm",
                   side_effect=fake_extract):
            nodes, edges, stats = await build_knowledge_graph(
                async_db_session, test_user_id, _fake_user(test_user_id)
            )

        assert stats["note_count"] == 1


# ────────────────────── save_kg_to_db / get_kg_from_db ──────────────────────

class TestSaveAndGetKg:
    @pytest.mark.asyncio
    async def test_save_and_get_roundtrip(self, async_db_session, test_user_id):
        # 先创建笔记（get_kg_from_db 需要查询收藏笔记）
        note = NoteDB(user_id=test_user_id, title="测试笔记", content="内容", is_favorite=1)
        async_db_session.add(note)
        await async_db_session.flush()

        nodes = [
            KGNode(id=f"note-{note.id}", label="测试笔记", type="note", note_id=note.id, weight=1.0),
            KGNode(id="concept-1", label="机器学习", type="concept", concept_id=1, weight=0.9,
                   preview="关联 1 篇笔记"),
        ]
        edges = [
            KGEdge(source=f"note-{note.id}", target=f"note-{note.id}", weight=0.5, type="note-note"),
            KGEdge(source="concept-1", target=f"note-{note.id}", weight=0.8, type="concept-note"),
        ]

        await save_kg_to_db(async_db_session, test_user_id, nodes, edges)

        # 设置状态为 ready
        await update_kg_status(async_db_session, test_user_id, "ready")

        result = await get_kg_from_db(async_db_session, test_user_id)
        assert result is not None
        got_nodes, got_edges, got_stats = result
        assert got_stats["note_count"] == 1
        assert got_stats["concept_count"] == 1
        assert got_stats["edge_count"] == 2

    @pytest.mark.asyncio
    async def test_get_kg_no_status_returns_none(self, async_db_session, test_user_id):
        result = await get_kg_from_db(async_db_session, test_user_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_kg_status_not_ready_returns_none(self, async_db_session, test_user_id):
        await update_kg_status(async_db_session, test_user_id, "processing")
        result = await get_kg_from_db(async_db_session, test_user_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_save_clears_existing_data(self, async_db_session, test_user_id):
        note = NoteDB(user_id=test_user_id, title="笔记", content="内容", is_favorite=1)
        async_db_session.add(note)
        await async_db_session.flush()

        # 第一次保存
        nodes1 = [KGNode(id="concept-1", label="旧概念", type="concept", concept_id=1, weight=0.5)]
        edges1 = [KGEdge(source="concept-1", target=f"note-{note.id}", weight=0.5, type="concept-note")]
        await save_kg_to_db(async_db_session, test_user_id, nodes1, edges1)

        # 第二次保存（应清除旧数据）
        nodes2 = [KGNode(id="concept-1", label="新概念", type="concept", concept_id=1, weight=0.9)]
        edges2 = [KGEdge(source="concept-1", target=f"note-{note.id}", weight=0.9, type="concept-note")]
        await save_kg_to_db(async_db_session, test_user_id, nodes2, edges2)

        await update_kg_status(async_db_session, test_user_id, "ready")
        result = await get_kg_from_db(async_db_session, test_user_id)
        assert result is not None
        _, _, stats = result
        assert stats["concept_count"] == 1

    @pytest.mark.asyncio
    async def test_edge_with_unknown_concept_skipped(self, async_db_session, test_user_id):
        note = NoteDB(user_id=test_user_id, title="笔记", content="内容", is_favorite=1)
        async_db_session.add(note)
        await async_db_session.flush()

        nodes = [KGNode(id=f"note-{note.id}", label="笔记", type="note", note_id=note.id)]
        # concept-99 不在 nodes 中，对应边应被跳过
        edges = [KGEdge(source="concept-99", target=f"note-{note.id}", weight=0.5, type="concept-note")]

        await save_kg_to_db(async_db_session, test_user_id, nodes, edges)
        await update_kg_status(async_db_session, test_user_id, "ready")

        result = await get_kg_from_db(async_db_session, test_user_id)
        assert result is not None
        _, got_edges, stats = result
        assert stats["edge_count"] == 0


# ────────────────────── update_kg_status / get_kg_status ──────────────────────

class TestKgStatus:
    @pytest.mark.asyncio
    async def test_create_status(self, async_db_session, test_user_id):
        await update_kg_status(async_db_session, test_user_id, "processing", progress=50, total_notes=10)
        status = await get_kg_status(async_db_session, test_user_id)
        assert status is not None
        assert status.status == "processing"
        assert status.progress == 50
        assert status.total_notes == 10

    @pytest.mark.asyncio
    async def test_update_existing_status(self, async_db_session, test_user_id):
        await update_kg_status(async_db_session, test_user_id, "processing", progress=10)
        await update_kg_status(async_db_session, test_user_id, "ready", progress=100, processed_notes=10)
        status = await get_kg_status(async_db_session, test_user_id)
        assert status.status == "ready"
        assert status.progress == 100
        assert status.processed_notes == 10

    @pytest.mark.asyncio
    async def test_unknown_kwargs_ignored(self, async_db_session, test_user_id):
        await update_kg_status(async_db_session, test_user_id, "ready", nonexistent_field="value")
        status = await get_kg_status(async_db_session, test_user_id)
        assert status.status == "ready"

    @pytest.mark.asyncio
    async def test_get_status_none_when_not_exists(self, async_db_session, test_user_id):
        status = await get_kg_status(async_db_session, test_user_id)
        assert status is None
