"""
知识图谱服务
- 概念提取：从笔记中提取核心概念
- 相似度计算：计算笔记之间的语义关联度
- 图谱生成：整合节点和边，生成完整知识图谱
"""
import re
import math
import asyncio
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.note import NoteDB
from app.models.kg import KGConceptDB, KGRelationDB, KGStatusDB, KGNode, KGEdge
from app.models.user import UserDB
from app.services.llm_runtime import openai_client_and_model_for_user
from app.core.logger import app_logger as logger


SIMILARITY_THRESHOLD = 0.35
MAX_RELATIONS_PER_NOTE = 5
MAX_CONCEPTS_PER_NOTE = 8
MIN_CONCEPT_NOTE_FREQ = 2
TITLE_WEIGHT = 3.0
MAX_NOTES_FOR_GRAPH = 100


def _clean_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;|&amp;|&lt;|&gt;|&quot;|&#\d+;', ' ', text)
    return text


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    text = _clean_html(text)
    text = re.sub(r'[^\w\u4e00-\u9fa5]', ' ', text.lower())
    words = [w for w in text.split() if len(w) >= 2]
    if not words:
        return []
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'can', 'shall', 'this', 'that',
        'these', 'those', 'it', 'its', 'they', 'them', 'their', 'we', 'our',
        'you', 'your', 'he', 'his', 'she', 'her', 'i', 'me', 'my', 'what',
        'which', 'who', 'whom', 'when', 'where', 'why', 'how', 'all', 'each',
        'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
        'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
        'very', 'just', 'also', 'now', 'here', 'there', 'then', 'once',
        '的', '了', '和', '是', '在', '我', '有', '就', '不', '人', '都',
        '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你',
        '会', '着', '没有', '看', '好', '自己', '这', '那', '什么', '怎么',
        '为什么', '可以', '因为', '所以', '但是', '然后', '如果', '虽然',
        '而且', '或者', '还是', '就是', '已经', '可能', '应该', '需要',
        '进行', '通过', '使用', '实现', '方法', '系统', '功能', '模块',
        '部分', '过程', '结果', '问题', '情况', '时候', '地方', '东西',
        '学习', '笔记', '总结', '介绍', '核心', '概念', '基础', '知识',
        '技术', '应用', '开发', '分析', '理解', '掌握', '重要', '主要',
        '以及', '及其', '等等', '相关', '不同', '各种', '一定', '具有',
        '提供', '支持', '基于', '对于', '关于', '根据', '通过', '在',
        '中', '的', '了', '和', '与', '或', '等', '及', '对', '从',
        '向', '由', '以', '为', '于', '是', '被', '将', '把', '让',
        '给', '向', '往', '从', '到', '在', '于', '自', '至', '沿',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'hr', 'div',
        'span', 'strong', 'em', 'b', 'i', 'u', 'ul', 'ol', 'li',
        'table', 'tr', 'td', 'th', 'img', 'a', 'code', 'pre',
        '学习笔记', '核心概念', '基本概念', '基础知识',
        '总结', '介绍', '分析', '概述', '简介', '说明',
        '第一章', '第二章', '第三章', '第一', '第二', '第三',
        '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
        '第', '章', '节', '点', '个', '项', '类', '种', '条',
    }
    return [w for w in words if w not in stop_words]


def _compute_tfidf(notes: List[NoteDB]) -> Tuple[Dict[int, Dict[str, float]], Dict[str, float]]:
    doc_count = len(notes)
    if doc_count == 0:
        return {}, {}

    word_doc_freq = defaultdict(int)
    note_word_counts = {}

    for note in notes:
        title_words = _tokenize(note.title or "")
        content_words = _tokenize(note.content or "")
        weighted_words = title_words * int(TITLE_WEIGHT) + content_words
        counter = Counter(weighted_words)
        note_word_counts[note.id] = counter
        for word in set(weighted_words):
            word_doc_freq[word] += 1

    idf = {}
    for word, df in word_doc_freq.items():
        idf[word] = math.log((doc_count + 1) / (df + 1)) + 1

    tfidf_vectors = {}
    for note_id, counter in note_word_counts.items():
        total = sum(counter.values())
        if total == 0:
            tfidf_vectors[note_id] = {}
            continue
        tfidf = {}
        for word, count in counter.items():
            tf = count / total
            tfidf[word] = tf * idf.get(word, 1.0)
        tfidf_vectors[note_id] = tfidf

    return tfidf_vectors, idf


def _cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    common_keys = set(vec_a.keys()) & set(vec_b.keys())
    if not common_keys:
        return 0.0
    dot_product = sum(vec_a[k] * vec_b[k] for k in common_keys)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


async def _extract_concepts_with_llm(note: NoteDB, db_user: UserDB) -> List[Tuple[str, float]]:
    try:
        client, model = openai_client_and_model_for_user(db_user)
        content = _clean_html(note.content)[:3000] if note.content else ""
        if not content.strip():
            return []
        prompt = f"""请从以下笔记内容中提取 5-8 个核心概念或关键词。

要求：
1. 概念要简洁，2-8个字最佳
2. 按重要程度排序
3. 只返回概念列表，每行一个，用"概念:权重"格式，权重0-1之间
4. 不要其他解释文字

笔记标题：{note.title}

笔记内容：
{content}
"""
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是专业的知识提取助手，擅长从文本中提取核心概念。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=500,
        )
        result_text = response.choices[0].message.content or ""
        concepts = []
        for line in result_text.strip().split('\n'):
            line = line.strip().lstrip('- ').lstrip('0123456789. ')
            if not line:
                continue
            if ':' in line:
                parts = line.split(':', 1)
                name = parts[0].strip()
                try:
                    weight = float(parts[1].strip())
                except ValueError:
                    weight = 0.5
            else:
                name = line.strip()
                weight = 0.5
            if 1 < len(name) < 20:
                concepts.append((name, min(max(weight, 0.1), 1.0)))
        return concepts[:MAX_CONCEPTS_PER_NOTE]
    except Exception as e:
        logger.info(f"LLM 概念提取失败，降级使用关键词提取: {e}")
        title_words = _tokenize(note.title or "")
        content_words = _tokenize(note.content or "")
        weighted_words = title_words * int(TITLE_WEIGHT) + content_words
        counter = Counter(weighted_words)
        total = len(weighted_words)
        if total == 0:
            return []
        keywords = {}
        for word, count in counter.most_common(MAX_CONCEPTS_PER_NOTE * 2):
            keywords[word] = count / total
        sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        return [(word, min(weight, 1.0)) for word, weight in sorted_keywords[:MAX_CONCEPTS_PER_NOTE]]


async def build_knowledge_graph(db: AsyncSession, user_id: int, db_user: UserDB) -> Tuple[List[KGNode], List[KGEdge], Dict]:
    result = await db.execute(
        select(NoteDB).where(NoteDB.user_id == user_id).order_by(NoteDB.updated_at.desc()).limit(MAX_NOTES_FOR_GRAPH)
    )
    notes = result.scalars().all()
    if not notes:
        return [], [], {"note_count": 0, "concept_count": 0, "edge_count": 0}

    tfidf_vectors, idf = _compute_tfidf(notes)

    edges = []
    note_ids = [n.id for n in notes]
    for i, note_a in enumerate(notes):
        similarities = []
        for j, note_b in enumerate(notes):
            if i >= j:
                continue
            sim = _cosine_similarity(tfidf_vectors.get(note_a.id, {}), tfidf_vectors.get(note_b.id, {}))
            if sim >= SIMILARITY_THRESHOLD:
                similarities.append((note_b.id, sim))
        similarities.sort(key=lambda x: x[1], reverse=True)
        for target_id, weight in similarities[:MAX_RELATIONS_PER_NOTE]:
            edges.append({
                "source": f"note-{note_a.id}",
                "target": f"note-{target_id}",
                "weight": round(weight, 3),
                "type": "note-note",
            })

    all_concepts: Dict[str, Dict] = defaultdict(lambda: {"weight": 0.0, "note_ids": []})
    concept_note_edges = []

    for note in notes:
        concepts = await _extract_concepts_with_llm(note, db_user)
        note_tfidf = tfidf_vectors.get(note.id, {})
        if not concepts and note_tfidf:
            sorted_tfidf = sorted(note_tfidf.items(), key=lambda x: x[1], reverse=True)
            top_concepts = [(w, min(v, 1.0)) for w, v in sorted_tfidf[:MAX_CONCEPTS_PER_NOTE]]
        else:
            enhanced = []
            for name, weight in concepts:
                name_lower = name.lower()
                extra_weight = note_tfidf.get(name_lower, 0) * 0.5
                enhanced.append((name, min(weight + extra_weight, 1.0)))
            top_concepts = enhanced
        for concept_name, weight in top_concepts:
            all_concepts[concept_name]["weight"] += weight
            all_concepts[concept_name]["note_ids"].append(note.id)
            concept_note_edges.append({
                "concept": concept_name,
                "note_id": note.id,
                "weight": round(weight, 3),
            })

    frequent_concepts = {
        name: data
        for name, data in all_concepts.items()
        if len(data["note_ids"]) >= MIN_CONCEPT_NOTE_FREQ
    }

    nodes = []
    for note in notes:
        content_preview = note.content[:150].replace('\n', ' ') if note.content else ""
        word_count = len(note.content) if note.content else 0
        size = max(20, min(60, 20 + word_count / 200))
        is_fav = bool(note.is_favorite) if note.is_favorite is not None else False
        color = "#ff6b6b" if is_fav else "#4facfe"
        nodes.append(KGNode(
            id=f"note-{note.id}",
            label=note.title,
            type="note",
            size=size,
            color=color,
            note_id=note.id,
            weight=1.0,
            preview=content_preview,
            tags=note.tags,
            is_favorite=is_fav,
            created_at=note.created_at.isoformat() if note.created_at else None,
            updated_at=note.updated_at.isoformat() if note.updated_at else None,
        ))

    concept_nodes = []
    concept_id_map = {}
    for idx, (name, data) in enumerate(frequent_concepts.items()):
        cid = idx + 1
        concept_id_map[name] = cid
        note_count = len(data["note_ids"])
        size = max(25, min(55, 25 + note_count * 3))
        concept_nodes.append(KGNode(
            id=f"concept-{cid}",
            label=name,
            type="concept",
            size=size,
            color="#a855f7",
            concept_id=cid,
            weight=round(data["weight"], 3),
            preview=f"关联 {note_count} 篇笔记",
        ))
    nodes.extend(concept_nodes)

    kg_edges = []
    for edge in edges:
        kg_edges.append(KGEdge(
            source=edge["source"],
            target=edge["target"],
            weight=edge["weight"],
            type=edge["type"],
        ))

    for edge in concept_note_edges:
        concept_name = edge["concept"]
        if concept_name not in concept_id_map:
            continue
        cid = concept_id_map[concept_name]
        kg_edges.append(KGEdge(
            source=f"concept-{cid}",
            target=f"note-{edge['note_id']}",
            weight=edge["weight"],
            type="concept-note",
        ))

    stats = {
        "note_count": len(notes),
        "concept_count": len(concept_nodes),
        "edge_count": len(kg_edges),
        "note_edges": len(edges),
        "concept_edges": len(kg_edges) - len(edges),
    }

    return nodes, kg_edges, stats


async def save_kg_to_db(db: AsyncSession, user_id: int, nodes: List[KGNode], edges: List[KGEdge]) -> None:
    await db.execute(delete(KGConceptDB).where(KGConceptDB.user_id == user_id))
    await db.execute(delete(KGRelationDB).where(KGRelationDB.user_id == user_id))

    concept_id_to_db_id = {}
    for node in nodes:
        if node.type == "concept":
            db_concept = KGConceptDB(
                user_id=user_id,
                name=node.label,
                weight=node.weight,
                source_note_ids="",
                description=node.preview,
            )
            db.add(db_concept)
            concept_id_to_db_id[node.id] = db_concept

    await db.flush()

    for node_id, db_concept in concept_id_to_db_id.items():
        concept_id_to_db_id[node_id] = db_concept.id

    for edge in edges:
        source_id = None
        target_id = None

        if edge.source.startswith("note-"):
            source_id = int(edge.source.replace("note-", ""))
        elif edge.source.startswith("concept-"):
            cid = concept_id_to_db_id.get(edge.source)
            if cid:
                source_id = int(cid)

        if edge.target.startswith("note-"):
            target_id = int(edge.target.replace("note-", ""))
        elif edge.target.startswith("concept-"):
            cid = concept_id_to_db_id.get(edge.target)
            if cid:
                target_id = int(cid)

        if source_id is not None and target_id is not None:
            db_relation = KGRelationDB(
                user_id=user_id,
                rel_type=edge.type,
                source_id=source_id,
                target_id=target_id,
                weight=edge.weight,
                label=edge.label,
            )
            db.add(db_relation)

    await db.commit()


async def get_kg_from_db(db: AsyncSession, user_id: int) -> Optional[Tuple[List[KGNode], List[KGEdge], Dict]]:
    result = await db.execute(
        select(KGStatusDB).where(KGStatusDB.user_id == user_id)
    )
    status = result.scalar_one_or_none()
    if not status or status.status != "ready":
        return None

    result_concepts = await db.execute(
        select(KGConceptDB).where(KGConceptDB.user_id == user_id)
    )
    concept_db_list = result_concepts.scalars().all()

    result_relations = await db.execute(
        select(KGRelationDB).where(KGRelationDB.user_id == user_id)
    )
    rel_db_list = result_relations.scalars().all()

    result_notes = await db.execute(
        select(NoteDB).where(NoteDB.user_id == user_id).order_by(NoteDB.updated_at.desc())
    )
    notes = result_notes.scalars().all()

    nodes = []
    note_id_map = {}
    for note in notes:
        content_preview = note.content[:150].replace('\n', ' ') if note.content else ""
        word_count = len(note.content) if note.content else 0
        size = max(20, min(60, 20 + word_count / 200))
        is_fav = bool(note.is_favorite) if note.is_favorite is not None else False
        color = "#ff6b6b" if is_fav else "#4facfe"
        node = KGNode(
            id=f"note-{note.id}",
            label=note.title,
            type="note",
            size=size,
            color=color,
            note_id=note.id,
            weight=1.0,
            preview=content_preview,
            tags=note.tags,
            is_favorite=is_fav,
            created_at=note.created_at.isoformat() if note.created_at else None,
            updated_at=note.updated_at.isoformat() if note.updated_at else None,
        )
        nodes.append(node)
        note_id_map[note.id] = node

    concept_nodes = []
    concept_id_map = {}
    for c in concept_db_list:
        note_count = len([r for r in rel_db_list if r.rel_type == "concept-note" and r.source_id == c.id])
        size = max(25, min(55, 25 + note_count * 3))
        node = KGNode(
            id=f"concept-{c.id}",
            label=c.name,
            type="concept",
            size=size,
            color="#a855f7",
            concept_id=c.id,
            weight=round(c.weight, 3),
            preview=c.description or f"关联 {note_count} 篇笔记",
        )
        concept_nodes.append(node)
        concept_id_map[c.id] = node
    nodes.extend(concept_nodes)

    edges = []
    note_edge_count = 0
    concept_edge_count = 0
    for rel in rel_db_list:
        if rel.rel_type == "note-note":
            source_id = f"note-{rel.source_id}"
            target_id = f"note-{rel.target_id}"
            note_edge_count += 1
        elif rel.rel_type == "concept-note":
            source_id = f"concept-{rel.source_id}"
            target_id = f"note-{rel.target_id}"
            concept_edge_count += 1
        else:
            continue
        edges.append(KGEdge(
            source=source_id,
            target=target_id,
            weight=rel.weight,
            type=rel.rel_type,
            label=rel.label,
        ))

    stats = {
        "note_count": len([n for n in nodes if n.type == "note"]),
        "concept_count": len(concept_nodes),
        "edge_count": len(edges),
        "note_edges": note_edge_count,
        "concept_edges": concept_edge_count,
    }

    return nodes, edges, stats


async def update_kg_status(db: AsyncSession, user_id: int, status: str, **kwargs) -> None:
    result = await db.execute(
        select(KGStatusDB).where(KGStatusDB.user_id == user_id)
    )
    db_status = result.scalar_one_or_none()
    if not db_status:
        db_status = KGStatusDB(user_id=user_id, status=status)
        db.add(db_status)
    else:
        db_status.status = status
    for key, value in kwargs.items():
        if hasattr(db_status, key):
            setattr(db_status, key, value)
    await db.commit()


async def get_kg_status(db: AsyncSession, user_id: int) -> Optional[KGStatusDB]:
    result = await db.execute(
        select(KGStatusDB).where(KGStatusDB.user_id == user_id)
    )
    return result.scalar_one_or_none()
