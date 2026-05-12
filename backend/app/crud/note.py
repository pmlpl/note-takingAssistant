from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.note import NoteDB
from typing import List, Optional


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


async def create_note(db: AsyncSession, user_id: int, title: str, content: str, tags: str = None, is_favorite: int = 1):
    """创建笔记"""
    db_note = NoteDB(
        user_id=user_id,
        title=title,
        content=content,
        tags=tags,
        is_favorite=is_favorite  # 默认为1（已加入我的笔记）
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
    """
    根据标题和内容查找笔记（用于去重）
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        title: 笔记标题
        content: 笔记内容
    
    Returns:
        Optional[NoteDB]: 如果找到返回笔记对象，否则返回None
    """
    # 查找相同用户、相同标题且内容相似度高的笔记
    # 这里使用精确匹配，也可以改为模糊匹配或哈希比较
    result = await db.execute(
        select(NoteDB).where(
            NoteDB.user_id == user_id,
            NoteDB.title == title,
            NoteDB.content == content
        )
    )
    return result.scalar_one_or_none()
