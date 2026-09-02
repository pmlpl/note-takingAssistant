"""AI 对话历史持久化 CRUD 操作

提供对 ai_conversations / ai_messages 表的基本增删查改。
所有操作均以 user_id 为隔离维度，防止跨用户访问。
"""

from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.sql import func

from app.core.database import AsyncSessionLocal  # noqa: F401 兼容导入
from app.models.ai_conversation import AIConversationDB, AIMessageDB


# ============== 对话 (Conversation) CRUD ==============
async def list_conversations(db, user_id: int, limit: int = 50) -> list[AIConversationDB]:
    """列出用户的全部对话，按 updated_at 倒序"""
    result = await db.execute(
        select(AIConversationDB)
        .where(AIConversationDB.user_id == user_id)
        .order_by(AIConversationDB.updated_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_conversation(db, conversation_id: int, user_id: int) -> Optional[AIConversationDB]:
    """获取单个对话（必须属于该用户）"""
    result = await db.execute(
        select(AIConversationDB).where(
            AIConversationDB.id == conversation_id,
            AIConversationDB.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_conversation(db, user_id: int, title: str) -> AIConversationDB:
    """创建新对话"""
    conv = AIConversationDB(user_id=user_id, title=title)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


async def rename_conversation(db, conversation_id: int, user_id: int, title: str) -> Optional[AIConversationDB]:
    """重命名对话标题"""
    await db.execute(
        update(AIConversationDB)
        .where(
            AIConversationDB.id == conversation_id,
            AIConversationDB.user_id == user_id,
        )
        .values(title=title, updated_at=func.now())
    )
    await db.commit()
    return await get_conversation(db, conversation_id, user_id)


async def delete_conversation(db, conversation_id: int, user_id: int) -> bool:
    """删除对话（包括其下所有消息）

    外键 ondelete=CASCADE 应自动级联删除消息，但有些环境可能未生效，这里手动清理一次。
    """
    conv = await get_conversation(db, conversation_id, user_id)
    if not conv:
        return False
    # 先删消息，再删对话，确保即使外键级联未启用也能清理
    await db.execute(delete(AIMessageDB).where(AIMessageDB.conversation_id == conversation_id))
    await db.execute(
        delete(AIConversationDB).where(
            AIConversationDB.id == conversation_id,
            AIConversationDB.user_id == user_id,
        )
    )
    await db.commit()
    return True


# ============== 消息 (Message) CRUD ==============
async def list_messages(db, conversation_id: int, user_id: int) -> list[AIMessageDB]:
    """列出某对话的全部消息（按时间正序）

    先校验 conversation 属于该用户，再查消息。
    """
    conv = await get_conversation(db, conversation_id, user_id)
    if not conv:
        return []
    result = await db.execute(
        select(AIMessageDB)
        .where(AIMessageDB.conversation_id == conversation_id)
        .order_by(AIMessageDB.created_at.asc(), AIMessageDB.id.asc())
    )
    return list(result.scalars().all())
