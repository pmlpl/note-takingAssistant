"""AI 对话历史持久化模型

对应数据库两张表：
- ai_conversations: 一个用户的多条对话（每条对话有标题和时间戳）
- ai_messages: 对话内的具体消息（user / assistant / tool）
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.sql import func

from app.core.database import Base


# ============== SQLAlchemy 数据库模型 ==============
class AIConversationDB(Base):
    """AI 对话表：一个用户可以有多个对话"""
    __tablename__ = "ai_conversations"
    __table_args__ = (
        Index("idx_ai_conv_user", "user_id"),
        Index("idx_ai_conv_user_updated", "user_id", "updated_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AIMessageDB(Base):
    """AI 消息表：保存对话内的每条消息"""
    __tablename__ = "ai_messages"
    __table_args__ = (
        Index("idx_ai_msg_conv", "conversation_id"),
        Index("idx_ai_msg_conv_created", "conversation_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer, ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(Text, nullable=False)  # user / assistant / tool
    content = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ============== Pydantic 响应模型 ==============
class AIMessageOut(BaseModel):
    """AI 消息响应"""
    id: int
    role: str
    content: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AIConversationOut(BaseModel):
    """AI 对话响应（列表项，不含消息）"""
    id: int
    title: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AIConversationDetailOut(AIConversationOut):
    """AI 对话详情（含全部消息）"""
    messages: List[AIMessageOut] = Field(default_factory=list)


class AIConversationCreateRequest(BaseModel):
    """新建对话请求"""
    title: Optional[str] = None  # 不传则用默认标题
