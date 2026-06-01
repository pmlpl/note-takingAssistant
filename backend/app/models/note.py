from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


# Pydantic模型
class NoteBase(BaseModel):
    title: str
    content: str
    tags: Optional[str] = None
    is_favorite: Optional[bool] = False  # 是否已加入"我的笔记"


class NoteCreate(NoteBase):
    # 新建笔记默认加入「我的笔记」列表（与 NoteList 仅展示 is_favorite=1 一致）
    is_favorite: Optional[bool] = True


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    is_favorite: Optional[bool] = None  # 是否已加入"我的笔记"


class NoteResponse(NoteBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        # 允许从字符串解析日期
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    @field_validator('is_favorite', mode='before')
    @classmethod
    def convert_is_favorite(cls, v):
        """将数据库的 Integer 转换为布尔值"""
        if isinstance(v, int):
            return bool(v)
        return v


# SQLAlchemy数据库模型
class NoteDB(Base):
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(String(500), nullable=True)
    is_favorite = Column(Integer, default=0)  # 0:未加入我的笔记, 1:已加入
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
