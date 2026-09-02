from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import NoteDB


async def get_note(db: AsyncSession, note_id: int, user_id: int):
    """获取用户的笔记"""
    result = await db.execute(select(NoteDB).where(NoteDB.id == note_id, NoteDB.user_id == user_id))
    return result.scalar_one_or_none()


async def get_notes(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100):
    """获取用户的笔记列表"""
    result = await db.execute(select(NoteDB).where(NoteDB.user_id == user_id).offset(skip).limit(limit))
    return result.scalars().all()


async def search_notes(
    db: AsyncSession,
    user_id: int,
    keyword: str = "",
    skip: int = 0,
    limit: int = 20,
    is_favorite: Optional[bool] = None,
):
    """关键词检索笔记（标题或正文模糊匹配，RAG 混合检索的 SQL 兜底），支持分页和收藏筛选"""
    query = select(NoteDB).where(NoteDB.user_id == user_id)
    if keyword:
        query = query.where(
            or_(
                NoteDB.title.ilike(f"%{keyword}%"),
                NoteDB.content.ilike(f"%{keyword}%"),
            )
        )
    if is_favorite is not None:
        query = query.where(NoteDB.is_favorite == (1 if is_favorite else 0))
    query = query.order_by(NoteDB.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def count_notes(
    db: AsyncSession,
    user_id: int,
    keyword: str = "",
    is_favorite: Optional[bool] = None,
) -> int:
    """统计符合条件的笔记总数（标题或正文模糊匹配，用于分页）"""
    query = select(func.count(NoteDB.id)).where(NoteDB.user_id == user_id)
    if keyword:
        query = query.where(
            or_(
                NoteDB.title.ilike(f"%{keyword}%"),
                NoteDB.content.ilike(f"%{keyword}%"),
            )
        )
    if is_favorite is not None:
        query = query.where(NoteDB.is_favorite == (1 if is_favorite else 0))
    result = await db.execute(query)
    return result.scalar() or 0


async def get_notes_by_ids(db: AsyncSession, user_id: int, ids: list[int]):
    """按 id 批量获取用户的笔记（RAG 混合排序后回表用）"""
    if not ids:
        return []
    result = await db.execute(select(NoteDB).where(NoteDB.user_id == user_id, NoteDB.id.in_(ids)))
    return result.scalars().all()


async def create_note(
    db: AsyncSession, user_id: int, title: str, content: str, tags: str = None, is_favorite: bool = True
):
    """创建笔记"""
    db_note = NoteDB(
        user_id=user_id,
        title=title,
        content=content,
        tags=tags,
        is_favorite=(1 if is_favorite else 0),
    )
    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)
    return db_note


async def update_note(
    db: AsyncSession,
    note_id: int,
    user_id: int,
    title: str = None,
    content: str = None,
    tags: str = None,
    is_favorite: bool = None,
):
    """更新笔记（任何字段变更都会提交，修复此前仅 is_favorite 变更才 commit 导致标题/正文更新丢失的问题）"""
    db_note = await get_note(db, note_id, user_id)
    if not db_note:
        return None
    if title is not None:
        db_note.title = title
    if content is not None:
        db_note.content = content
    if tags is not None:
        db_note.tags = tags
    if is_favorite is not None:
        db_note.is_favorite = 1 if is_favorite else 0
    await db.commit()
    await db.refresh(db_note)
    return db_note


async def delete_note(db: AsyncSession, note_id: int, user_id: int):
    """删除笔记（同事务内先删 RAG 分块，避免外键约束阻塞）"""
    db_note = await get_note(db, note_id, user_id)
    if db_note:
        from app.crud import note_chunk as crud_note_chunk

        await crud_note_chunk.delete_chunks_for_note(db, user_id, note_id)
        await db.delete(db_note)
        await db.commit()
    return db_note


async def get_note_by_title_and_content(
    db: AsyncSession, user_id: int, title: str, content: str
) -> type[NoteDB] | None:
    result = await db.execute(
        select(NoteDB).where(NoteDB.user_id == user_id, NoteDB.title == title, NoteDB.content == content)
    )
    return result.scalar_one_or_none()


async def get_note_by_title(db: AsyncSession, user_id: int, title: str) -> type[NoteDB] | None:
    """按 (user_id, title) 精确查询，用于重复标题检测。"""
    result = await db.execute(
        select(NoteDB)
        .where(
            NoteDB.user_id == user_id,
            NoteDB.title == title,
        )
        .limit(1)
    )
    return result.scalar_one_or_none()
