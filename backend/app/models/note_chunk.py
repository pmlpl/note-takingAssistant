from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.sql import func

from app.core.database import Base


class NoteChunkDB(Base):
    """笔记分块（RAG 检索单元）。

    embedding 以 JSON 数组文本存储（如 [0.012, -0.034, ...]），
    数据量小，检索时整体加载后在 Python 内做余弦相似度，
    不需要 MySQL 侧向量能力。
    """

    __tablename__ = "note_chunks"
    __table_args__ = (Index("idx_note_chunks_user_note", "user_id", "note_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)  # 块在笔记内的顺序
    content = Column(Text, nullable=False)  # 块文本（不含 HTML 标签）
    embedding = Column(Text, nullable=True)  # JSON 数组；embedding 不可用时为 NULL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
