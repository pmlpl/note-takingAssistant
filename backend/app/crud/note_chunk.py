"""note_chunks 表（RAG 分块）的数据库操作。"""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note_chunk import NoteChunkDB


async def get_chunks_for_note(db: AsyncSession, user_id: int, note_id: int):
    """获取某笔记的全部分块（按 chunk_index 升序）"""
    result = await db.execute(
        select(NoteChunkDB)
        .where(NoteChunkDB.user_id == user_id, NoteChunkDB.note_id == note_id)
        .order_by(NoteChunkDB.chunk_index)
    )
    return result.scalars().all()


async def get_all_chunks_for_user(db: AsyncSession, user_id: int):
    """获取用户的全部分块（数据量小，整表加载后在 Python 内检索）"""
    result = await db.execute(select(NoteChunkDB).where(NoteChunkDB.user_id == user_id))
    return result.scalars().all()


async def delete_chunks_for_note(db: AsyncSession, user_id: int, note_id: int) -> None:
    """删除某笔记的全部分块"""
    await db.execute(delete(NoteChunkDB).where(NoteChunkDB.user_id == user_id, NoteChunkDB.note_id == note_id))


async def add_chunks(db: AsyncSession, chunks: list[NoteChunkDB]) -> None:
    """批量插入分块"""
    if chunks:
        db.add_all(chunks)


async def count_chunks_for_user(db: AsyncSession, user_id: int) -> int:
    """统计用户分块总数（rebuild 接口用）"""
    from sqlalchemy import func

    result = await db.execute(select(func.count(NoteChunkDB.id)).where(NoteChunkDB.user_id == user_id))
    return result.scalar() or 0
