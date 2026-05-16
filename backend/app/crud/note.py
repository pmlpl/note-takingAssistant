from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.note import NoteDB
from typing import Optional


async def get_note(db: AsyncSession, note_id: int, user_id: int):
    """获取用户的笔记"""
    result = await db.execute(
        select(NoteDB).where(NoteDB.id == note_id, NoteDB.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_notes(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100):
    """获取用户的笔记列表"""
    result = await db.execute(
        select(NoteDB).where(NoteDB.user_id == user_id).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def search_notes(
    db: AsyncSession,
    user_id: int,
    keyword: str = "",
    skip: int = 0,
    limit: int = 20,
    is_favorite: Optional[bool] = None,
):
    """搜索笔记（仅按标题模糊匹配），支持分页和收藏筛选"""
    query = select(NoteDB).where(NoteDB.user_id == user_id)
    if keyword:
        query = query.where(
                NoteDB.title.ilike(f"%{keyword}%")
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
    """统计符合条件的笔记总数（用于分页）"""
    query = select(func.count(NoteDB.id)).where(NoteDB.user_id == user_id)
    if keyword:
        query = query.where(NoteDB.title.ilike(f"%{keyword}%"))
    if is_favorite is not None:
        query = query.where(NoteDB.is_favorite == (1 if is_favorite else 0))
    result = await db.execute(query)
    return result.scalar() or 0


async def create_note(db: AsyncSession, user_id: int, title: str, content: str, tags: str = None, is_favorite: int = 1):
    """创建笔记"""
    db_note = NoteDB(
        user_id=user_id,
        title=title,
        content=content,
        tags=tags,
        is_favorite=is_favorite
    )
    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)
    return db_note


async def update_note(db: AsyncSession, note_id: int, user_id: int, title: str = None, content: str = None, tags: str = None, is_favorite: int = None):
    """更新笔记"""
    db_note = await get_note(db, note_id, user_id)
    if db_note:
        if title is not None:
            db_note.title = title
        if content is not None:
            db_note.content = content
        if tags is not None:
            db_note.tags = tags
        if is_favorite is not None:
            db_note.is_favorite = is_favorite
        await db.commit()
        await db.refresh(db_note)
    return db_note


async def delete_note(db: AsyncSession, note_id: int, user_id: int):
    """删除笔记"""
    db_note = await get_note(db, note_id, user_id)
    if db_note:
        await db.delete(db_note)
        await db.commit()
    return db_note


async def get_note_by_title_and_content(db: AsyncSession, user_id: int, title: str, content: str) -> type[NoteDB] | None:
    result = await db.execute(
        select(NoteDB).where(
            NoteDB.user_id == user_id,
            NoteDB.title == title,
            NoteDB.content == content
        )
    )
    return result.scalar_one_or_none()
