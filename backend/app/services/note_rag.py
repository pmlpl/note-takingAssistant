"""轻量 RAG：分块 + embedding + 向量/关键词混合检索。

- 分块：按标题/段落简单切分（笔记量小，不需要复杂分块器）
- embedding：复用 OpenAI 兼容接口（/v1/embeddings，与 chat 同一套 BYOK 配置）；
  embedding 不可用时优雅降级为纯关键词检索，不影响笔记 CRUD
- 检索：纯 Python 余弦相似度 + 关键词（title/content ilike）混合排序
- 索引维护：创建/更新/删除笔记时同步 chunk；提供 rebuild 入口

ponytail: 数据量大后把「整表加载 + Python 余弦」换成 numpy 向量化余弦，
         再往后可平滑迁移到 pgvector / milvus 等向量库——分块与检索接口保持不变。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import note as crud_note
from app.crud import note_chunk as crud_note_chunk
from app.models.note_chunk import NoteChunkDB
from app.services.llm_runtime import openai_client_and_model_for_user, resolve_llm_model

logger = logging.getLogger(__name__)

# 单块最大字符数（按段落累计切分）
CHUNK_MAX_CHARS = 500
# 混合排序权重：标题精确命中 > 正文关键词 > 向量语义
TITLE_MATCH_WEIGHT = 1.0
CONTENT_MATCH_WEIGHT = 0.5
VECTOR_MATCH_WEIGHT = 0.7
# 关键词检索最多收集的候选笔记数（混合排序在内存中进行）
MAX_KEYWORD_CANDIDATES = 200

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(content: str) -> str:
    """去掉 HTML 标签，返回纯文本。"""
    return _HTML_TAG_RE.sub("", content or "")


def chunk_note_content(title: str, content: str, max_chars: int = CHUNK_MAX_CHARS) -> list[str]:
    """按标题/段落简单切分笔记。

    第 0 块包含标题；正文按空行分段，段落累计到 max_chars 时切下一块。
    """
    text = strip_html(content).replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    if (title or "").strip():
        chunks.append(title.strip())

    buffer = ""
    for para in paragraphs:
        candidate = para if not buffer else buffer + "\n" + para
        if len(candidate) <= max_chars:
            buffer = candidate
            continue
        if buffer:
            chunks.append(buffer)
            buffer = ""
        # 单段超长时按字符硬切
        for i in range(0, len(para), max_chars):
            chunks.append(para[i : i + max_chars])
    if buffer:
        chunks.append(buffer)

    if not chunks:
        text = (title or "").strip() or (content or "").strip()
        if text:
            chunks.append(text)
    return chunks


def resolve_embedding_model(db_user) -> str:
    """embedding 模型名：优先 EMBEDDING_MODEL，未配置时与对话模型一致。"""
    from app.core.config import settings

    name = (settings.EMBEDDING_MODEL or "").strip()
    return name or resolve_llm_model(db_user)


async def embed_texts(db_user, texts: list[str]) -> Optional[list[list[float]]]:
    """调用 OpenAI 兼容 /embeddings 接口；失败返回 None（调用方降级为纯关键词）。"""
    if not texts:
        return []
    try:
        client, _ = openai_client_and_model_for_user(db_user)
        model = resolve_embedding_model(db_user)
        resp = await client.embeddings.create(model=model, input=texts)
        return [d.embedding for d in resp.data]
    except Exception as e:
        # 常见原因：模型服务未加载 embedding 模型 / 接口不支持 / 网络不通
        logger.info(f"embedding 不可用，降级为纯关键词检索: {e}")
        return None


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """纯 Python 余弦相似度（数据量小，不引 numpy）。"""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _chunk_embedding(chunk: NoteChunkDB) -> Optional[list[float]]:
    if not chunk.embedding:
        return None
    try:
        return json.loads(chunk.embedding)
    except (ValueError, TypeError):
        return None


def _score_chunks(
    chunks: list[NoteChunkDB], query: str, query_embedding: Optional[list[float]]
) -> list[dict[str, Any]]:
    """对分块打分：关键词命中 + 向量余弦，返回 [{chunk, score, source}]。

    source: hybrid（关键词+向量都命中）/ keyword / vector / none
    """
    q = (query or "").strip().lower()
    scored: list[dict[str, Any]] = []
    for chunk in chunks:
        text = (chunk.content or "").lower()
        kw_score = 1.0 if q and q in text else 0.0
        vec_score = 0.0
        emb = _chunk_embedding(chunk)
        if query_embedding and emb:
            vec_score = _cosine_similarity(query_embedding, emb)
        score = TITLE_MATCH_WEIGHT * kw_score + VECTOR_MATCH_WEIGHT * vec_score
        if kw_score and vec_score > 0:
            source = "hybrid"
        elif kw_score:
            source = "keyword"
        elif vec_score > 0:
            source = "vector"
        else:
            source = "none"
        scored.append({"chunk": chunk, "score": score, "vec_score": vec_score, "source": source})
    scored.sort(key=lambda x: (-x["score"], x["chunk"].chunk_index))
    return scored


async def _embed_query(db_user, query: str) -> Optional[list[float]]:
    """查询向量；空查询或不支持 embedding 时返回 None。"""
    q = (query or "").strip()
    if not q:
        return None
    vecs = await embed_texts(db_user, [q])
    return vecs[0] if vecs else None


# ============== 索引维护 ==============
async def index_note_chunks(db: AsyncSession, db_user, note) -> dict[str, Any]:
    """同步单篇笔记的分块索引（先删后插），失败不抛异常、不影响笔记 CRUD。"""
    note_id = int(note.id)
    await crud_note_chunk.delete_chunks_for_note(db, db_user.id, note_id)
    chunks = chunk_note_content(note.title, note.content)
    embeddings: Optional[list[list[float]]] = None
    if chunks:
        embeddings = await embed_texts(db_user, chunks)
    rows = [
        NoteChunkDB(
            user_id=db_user.id,
            note_id=note_id,
            chunk_index=i,
            content=text,
            embedding=json.dumps(embeddings[i], ensure_ascii=False) if embeddings else None,
        )
        for i, text in enumerate(chunks)
    ]
    await crud_note_chunk.add_chunks(db, rows)
    await db.commit()
    return {"note_id": note_id, "chunks": len(rows), "embedded": embeddings is not None}


async def delete_note_chunks(db: AsyncSession, user_id: int, note_id: int) -> None:
    """删除单篇笔记的分块索引（笔记删除时调用）。"""
    await crud_note_chunk.delete_chunks_for_note(db, user_id, note_id)
    await db.commit()


async def rebuild_all_note_chunks(db: AsyncSession, db_user) -> dict[str, Any]:
    """重建用户全部笔记的分块索引，返回统计信息。"""
    notes = await crud_note.get_notes(db, user_id=db_user.id, skip=0, limit=10000)
    total_chunks = 0
    embedded_notes = 0
    for note in notes:
        result = await index_note_chunks(db, db_user, note)
        total_chunks += result["chunks"]
        if result["embedded"]:
            embedded_notes += 1
    return {
        "total_notes": len(notes),
        "total_chunks": total_chunks,
        "embedded_notes": embedded_notes,
    }


# ============== 检索 ==============
async def hybrid_search_notes(
    db: AsyncSession,
    db_user,
    keyword: str = "",
    skip: int = 0,
    limit: int = 20,
    is_favorite: Optional[bool] = None,
) -> tuple[list, int]:
    """混合检索笔记：关键词（title/content ilike）+ 向量语义，返回 (笔记列表, 总数)。

    标题命中权重最高，保证原有标题搜索不退化；无关键词时退化为普通列表。
    """
    q = (keyword or "").strip()
    scores: dict[int, float] = {}
    candidate_ids: set[int] = set()

    if q:
        # 1) 关键词候选（SQL 兜底，兼容未建索引的历史笔记）
        keyword_notes = await crud_note.search_notes(
            db, user_id=db_user.id, keyword=q, skip=0, limit=MAX_KEYWORD_CANDIDATES, is_favorite=is_favorite
        )
        for note in keyword_notes:
            title_hit = q.lower() in (note.title or "").lower()
            scores[note.id] = TITLE_MATCH_WEIGHT if title_hit else CONTENT_MATCH_WEIGHT
            candidate_ids.add(note.id)

        # 2) 向量候选（按分块余弦聚合到笔记；关键词权重已由第 1 步计算，这里只加向量分量）
        query_embedding = await _embed_query(db_user, q)
        if query_embedding:
            chunks = await crud_note_chunk.get_all_chunks_for_user(db, db_user.id)
            note_best: dict[int, float] = {}
            for item in _score_chunks(chunks, q, query_embedding):
                if item["vec_score"] > 0:
                    chunk = item["chunk"]
                    note_best[chunk.note_id] = max(note_best.get(chunk.note_id, 0.0), item["vec_score"])
            for note_id, vec_score in note_best.items():
                scores[note_id] = scores.get(note_id, 0.0) + VECTOR_MATCH_WEIGHT * vec_score
                candidate_ids.add(note_id)

    # 3) 拉取候选笔记并按分数排序、分页
    if not candidate_ids:
        notes = await crud_note.get_notes(db, user_id=db_user.id, skip=0, limit=MAX_KEYWORD_CANDIDATES)
        if is_favorite is not None:
            notes = [n for n in notes if (n.is_favorite or 0) == (1 if is_favorite else 0)]
        total = len(notes)
        page = sorted(notes, key=_note_sort_key, reverse=True)[skip : skip + limit]
        return page, total

    notes_by_id: dict[int, Any] = {}
    page_notes = await crud_note.get_notes_by_ids(db, user_id=db_user.id, ids=list(candidate_ids))
    for n in page_notes:
        if is_favorite is not None and (n.is_favorite or 0) != (1 if is_favorite else 0):
            continue
        notes_by_id[n.id] = n

    ranked = sorted(notes_by_id.values(), key=lambda n: (scores.get(n.id, 0.0), _note_sort_key(n)), reverse=True)
    total = len(ranked)
    return ranked[skip : skip + limit], total


def _note_sort_key(note) -> tuple:
    updated = getattr(note, "updated_at", None) or getattr(note, "created_at", None)
    return (updated, note.id)


async def retrieve_context(
    db: AsyncSession,
    db_user,
    query: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """检索与 query 相关的笔记片段（AI 对话上下文注入用）。

    优先基于分块做向量+关键词混合排序；用户还没有任何分块时，
    退化为笔记级关键词匹配并截取开头片段。
    """
    q = (query or "").strip()
    if not q:
        return []
    limit = max(1, min(limit, 10))

    chunks = await crud_note_chunk.get_all_chunks_for_user(db, db_user.id)
    if not chunks:
        # 历史笔记尚未建索引：笔记级关键词兜底
        notes = await crud_note.search_notes(db, user_id=db_user.id, keyword=q, skip=0, limit=limit)
        return [
            {
                "note_id": n.id,
                "note_title": n.title,
                "chunk_index": 0,
                "content": (n.content or "")[:CHUNK_MAX_CHARS],
                "score": TITLE_MATCH_WEIGHT if q.lower() in (n.title or "").lower() else CONTENT_MATCH_WEIGHT,
                "source": "keyword",
            }
            for n in notes
        ]

    query_embedding = await _embed_query(db_user, q)
    scored = _score_chunks(chunks, q, query_embedding)
    top = [item for item in scored if item["score"] > 0][:limit]
    if not top:
        return []

    note_ids = sorted({item["chunk"].note_id for item in top})
    notes_by_id = {n.id: n for n in await crud_note.get_notes_by_ids(db, db_user.id, note_ids)}
    items = []
    for item in top:
        note = notes_by_id.get(item["chunk"].note_id)
        if note is None:
            continue  # 防御：笔记已删但分块残留（孤儿分块）时跳过
        items.append(
            {
                "note_id": item["chunk"].note_id,
                "note_title": note.title,
                "chunk_index": item["chunk"].chunk_index,
                "content": item["chunk"].content,
                "score": round(item["score"], 4),
                "source": item["source"],
            }
        )
    return items
