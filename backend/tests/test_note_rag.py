"""RAG 笔记语义检索测试：分块、索引同步、混合检索、上下文检索、Agent 工具与 API。

embedding 调用全部通过 monkeypatch 替换为确定性伪向量，不依赖外部模型服务。
"""

import json

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.crud import note as crud_note
from app.crud import note_chunk as crud_note_chunk
from app.services import note_rag
from main import app


@pytest_asyncio.fixture(autouse=True)
async def _ensure_note_chunks_table():
    """DB 直连测试不经过 TestClient lifespan，需确保 note_chunks 表已创建（幂等）。

    用独立 engine 避免与全局 engine 的事件循环串池。
    """
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.core.config import settings
    from app.core.database import Base

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    finally:
        await engine.dispose()
    yield


class _FakeDBUser:
    id = 1


def _make_user(user_id: int) -> _FakeDBUser:
    u = _FakeDBUser()
    u.id = user_id
    return u


def _fake_embedding(texts):
    """确定性伪 embedding：机器学习主题 → [1,0]，美食主题 → [0,1]，其余 → [0.5,0.5]。"""
    out = []
    for t in texts:
        if "机器" in t or "深度学习" in t or "神经" in t:
            out.append([1.0, 0.0])
        elif "美食" in t or "烹饪" in t:
            out.append([0.0, 1.0])
        else:
            out.append([0.5, 0.5])
    return out


async def _fake_embed_texts(db_user, texts):
    return _fake_embedding(texts)


async def _no_embed(db_user, texts):
    """embedding 不可用（降级场景）"""
    return None


async def _create_note(db, user_id: int, title: str, content: str, is_favorite=1):
    return await crud_note.create_note(db, user_id=user_id, title=title, content=content, is_favorite=is_favorite)


# ============== 分块 ==============
def test_chunk_note_content_basic():
    chunks = note_rag.chunk_note_content("标题", "第一段。\n\n第二段。\n\n第三段。")
    assert chunks[0] == "标题"
    # 短段落累计合并为一个块（不超过 max_chars）
    assert len(chunks) == 2
    assert "第一段。" in chunks[1] and "第三段。" in chunks[1]


def test_chunk_note_content_max_chars():
    chunks = note_rag.chunk_note_content("T", "段" * 1200, max_chars=500)
    # 标题 + 1200 字符按 500 硬切为 3 块
    assert len(chunks) == 4
    assert all(len(c) <= 500 for c in chunks[1:])


def test_chunk_note_content_strips_html():
    chunks = note_rag.chunk_note_content("T", "<p>hello <b>world</b></p>")
    assert "hello world" in chunks


def test_chunk_note_content_empty():
    assert note_rag.chunk_note_content("", "") == []
    assert note_rag.chunk_note_content("仅标题", "") == ["仅标题"]


def test_cosine_similarity():
    assert note_rag._cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert note_rag._cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert note_rag._cosine_similarity([1.0, 0.0], []) == 0.0


# ============== 索引同步 ==============
async def test_index_sync_lifecycle(async_db_session, test_user_id, monkeypatch):
    monkeypatch.setattr(note_rag, "embed_texts", _fake_embed_texts)
    db_user = _make_user(test_user_id)
    note = await _create_note(async_db_session, test_user_id, "RAG测试", "第一段。\n\n第二段关于机器学习的描述。")

    result = await note_rag.index_note_chunks(async_db_session, db_user, note)
    assert result["chunks"] == 2  # 标题 + 合并后的正文块
    assert result["embedded"] is True
    chunks = await crud_note_chunk.get_chunks_for_note(async_db_session, test_user_id, note.id)
    assert [c.chunk_index for c in chunks] == [0, 1]
    assert json.loads(chunks[0].embedding) == [0.5, 0.5]  # 标题不含主题词
    assert json.loads(chunks[1].embedding) == [1.0, 0.0]  # 机器学习段

    # 更新内容后重建索引
    note.content = "全部改成关于美食烹饪的内容。"
    result2 = await note_rag.index_note_chunks(async_db_session, db_user, note)
    assert result2["chunks"] == 2
    chunks2 = await crud_note_chunk.get_chunks_for_note(async_db_session, test_user_id, note.id)
    assert len(chunks2) == 2
    assert "美食" in chunks2[1].content

    # 删除索引
    await note_rag.delete_note_chunks(async_db_session, test_user_id, note.id)
    chunks3 = await crud_note_chunk.get_chunks_for_note(async_db_session, test_user_id, note.id)
    assert chunks3 == []


async def test_index_sync_without_embedding_keeps_keyword_chunks(async_db_session, test_user_id, monkeypatch):
    """embedding 不可用时仍落库正文分块（关键词检索可用），不报错"""
    monkeypatch.setattr(note_rag, "embed_texts", _no_embed)
    db_user = _make_user(test_user_id)
    note = await _create_note(async_db_session, test_user_id, "降级笔记", "正文关键词仍可检索")
    result = await note_rag.index_note_chunks(async_db_session, db_user, note)
    assert result["chunks"] == 2
    assert result["embedded"] is False
    chunks = await crud_note_chunk.get_chunks_for_note(async_db_session, test_user_id, note.id)
    assert all(c.embedding is None for c in chunks)


# ============== 混合检索 ==============
async def test_hybrid_search_content_keyword_hit(async_db_session, test_user_id, monkeypatch):
    """正文关键词能命中（验收标准 1）"""
    monkeypatch.setattr(note_rag, "embed_texts", _no_embed)
    db_user = _make_user(test_user_id)
    await _create_note(async_db_session, test_user_id, "普通标题", "这里讲的是机器学习的训练方法")
    notes, total = await note_rag.hybrid_search_notes(async_db_session, db_user, keyword="训练方法")
    assert total == 1
    assert notes[0].title == "普通标题"


async def test_hybrid_search_title_not_regressed(async_db_session, test_user_id, monkeypatch):
    """标题命中权重高于正文命中（验收标准 1：标题搜索不退化）"""
    monkeypatch.setattr(note_rag, "embed_texts", _no_embed)
    db_user = _make_user(test_user_id)
    title_note = await _create_note(async_db_session, test_user_id, "机器学习入门", "其他内容")
    content_note = await _create_note(async_db_session, test_user_id, "其他标题", "机器学习是一门学科")
    notes, total = await note_rag.hybrid_search_notes(async_db_session, db_user, keyword="机器学习")
    assert total == 2
    assert notes[0].id == title_note.id
    assert notes[1].id == content_note.id


async def test_hybrid_search_pure_vector_hit(async_db_session, test_user_id, monkeypatch):
    """无关键词重合时，向量语义也能命中（验收标准 1 的语义部分）"""
    monkeypatch.setattr(note_rag, "embed_texts", _fake_embed_texts)
    db_user = _make_user(test_user_id)
    note_a = await _create_note(async_db_session, test_user_id, "AI笔记", "深度学习与机器学习的区别")
    note_b = await _create_note(async_db_session, test_user_id, "美食笔记", "烹饪技巧与美食探店")
    await note_rag.index_note_chunks(async_db_session, db_user, note_a)
    await note_rag.index_note_chunks(async_db_session, db_user, note_b)

    # "神经网络" 不出现于任何笔记正文，仅靠向量相似命中 note_a
    notes, total = await note_rag.hybrid_search_notes(async_db_session, db_user, keyword="神经网络")
    assert total == 1
    assert notes[0].id == note_a.id


async def test_hybrid_search_favorite_filter(async_db_session, test_user_id, monkeypatch):
    monkeypatch.setattr(note_rag, "embed_texts", _no_embed)
    db_user = _make_user(test_user_id)
    await _create_note(async_db_session, test_user_id, "收藏相关", "机器学习内容", is_favorite=1)
    await _create_note(async_db_session, test_user_id, "未收藏相关", "机器学习内容", is_favorite=0)
    notes, total = await note_rag.hybrid_search_notes(async_db_session, db_user, keyword="机器学习", is_favorite=True)
    assert total == 1
    assert notes[0].title == "收藏相关"


async def test_hybrid_search_pagination(async_db_session, test_user_id, monkeypatch):
    monkeypatch.setattr(note_rag, "embed_texts", _no_embed)
    db_user = _make_user(test_user_id)
    for i in range(3):
        await _create_note(async_db_session, test_user_id, f"分页{i}", "相同正文关键词")
    page1, total = await note_rag.hybrid_search_notes(
        async_db_session, db_user, keyword="相同正文关键词", skip=0, limit=2
    )
    page2, _ = await note_rag.hybrid_search_notes(async_db_session, db_user, keyword="相同正文关键词", skip=2, limit=2)
    assert total == 3
    assert len(page1) == 2
    assert len(page2) == 1
    assert len({n.id for n in page1} & {n.id for n in page2}) == 0
    assert len({n.id for n in page1} | {n.id for n in page2}) == 3


# ============== 上下文检索 ==============
async def test_retrieve_context_returns_chunks(async_db_session, test_user_id, monkeypatch):
    monkeypatch.setattr(note_rag, "embed_texts", _fake_embed_texts)
    db_user = _make_user(test_user_id)
    note = await _create_note(
        async_db_session, test_user_id, "学习笔记", "机器学习基础概念。\n\n这是关于美食的第二段。"
    )
    await note_rag.index_note_chunks(async_db_session, db_user, note)

    items = await note_rag.retrieve_context(async_db_session, db_user, "深度学习", limit=2)
    assert items
    assert items[0]["note_id"] == note.id
    assert items[0]["note_title"] == "学习笔记"
    assert items[0]["source"] in ("vector", "hybrid")
    assert items[0]["content"]

    # 关键词命中片段排最前（短段落合并为同一块时可能仅关键词命中）
    items2 = await note_rag.retrieve_context(async_db_session, db_user, "美食", limit=2)
    assert items2
    assert "美食" in items2[0]["content"]
    assert items2[0]["source"] in ("keyword", "hybrid")


async def test_retrieve_context_fallback_without_chunks(async_db_session, test_user_id, monkeypatch):
    """历史笔记未建索引时，退化为笔记级关键词匹配"""
    monkeypatch.setattr(note_rag, "embed_texts", _no_embed)
    db_user = _make_user(test_user_id)
    await _create_note(async_db_session, test_user_id, "历史笔记", "旧内容没有索引")
    items = await note_rag.retrieve_context(async_db_session, db_user, "历史笔记", limit=3)
    assert items
    assert items[0]["note_title"] == "历史笔记"
    assert items[0]["source"] == "keyword"


# ============== Agent 工具 ==============
async def test_agent_search_tool_uses_hybrid(async_db_session, test_user_id, monkeypatch):
    """search_notes 工具按正文关键词即可命中（验收标准 2）"""
    from app.services.agent.note_assistant import _tool_search_notes

    monkeypatch.setattr(note_rag, "embed_texts", _no_embed)
    db_user = _make_user(test_user_id)
    note = await _create_note(async_db_session, test_user_id, "工具笔记", "正文是量子计算的入门")
    result = await _tool_search_notes(
        db=async_db_session, user_id=test_user_id, args={"query": "量子计算"}, db_user=db_user
    )
    assert result["count"] == 1
    assert result["items"][0]["id"] == note.id
    assert "量子计算" in result["items"][0]["preview"]


# ============== API 接口 ==============
@pytest.fixture
def client():
    """每个测试用 with 触发 lifespan，确保 note_chunks 表已创建"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_token(client):
    import os

    email = f"rag_{__name__}_{os.urandom(4).hex()}@example.com"
    r = client.post("/api/v1/user/register", json={"email": email, "password": "Test123456", "nickname": "raguser"})
    assert r.status_code == 200
    r = client.post("/api/v1/user/login", json={"email": email, "password": "Test123456"})
    assert r.status_code == 200
    return r.json()["access_token"]


def _headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


def test_search_endpoint_hits_body_content(client, auth_token, monkeypatch):
    """笔记搜索接口：正文关键词可命中"""
    monkeypatch.setattr(note_rag, "embed_texts", _no_embed)
    headers = _headers(auth_token)
    r = client.post(
        "/api/v1/note/",
        headers=headers,
        json={"title": "接口标题", "content": "正文包含龙猫饲养技巧", "is_favorite": True},
    )
    assert r.status_code == 200

    r = client.get("/api/v1/note/search", headers=headers, params={"keyword": "龙猫"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "接口标题"
    assert data["total_pages"] == 1


def test_rag_context_endpoint(client, auth_token, monkeypatch):
    """RAG 上下文接口返回相关片段"""
    monkeypatch.setattr(note_rag, "embed_texts", _fake_embed_texts)
    headers = _headers(auth_token)
    r = client.post(
        "/api/v1/note/",
        headers=headers,
        json={"title": "上下文笔记", "content": "机器学习与深度学习的区别", "is_favorite": True},
    )
    assert r.status_code == 200

    r = client.get("/api/v1/note/rag/context", headers=headers, params={"query": "深度学习", "limit": 3})
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 1
    assert data["items"][0]["note_title"] == "上下文笔记"
    assert data["items"][0]["content"]


def test_rag_rebuild_endpoint(client, auth_token, monkeypatch):
    """重建索引接口：统计信息正确"""
    monkeypatch.setattr(note_rag, "embed_texts", _fake_embed_texts)
    headers = _headers(auth_token)
    for i in range(2):
        r = client.post(
            "/api/v1/note/",
            headers=headers,
            json={"title": f"重建笔记{i}", "content": f"机器学习内容{i}", "is_favorite": True},
        )
        assert r.status_code == 200

    r = client.post("/api/v1/note/rag/rebuild", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_notes"] == 2
    assert data["total_chunks"] >= 4  # 每篇至少 标题+正文 2 块
    assert data["embedded_notes"] == 2


def test_rag_context_requires_auth(client):
    r = client.get("/api/v1/note/rag/context", params={"query": "x"})
    assert r.status_code == 401
    r = client.post("/api/v1/note/rag/rebuild")
    assert r.status_code == 401
