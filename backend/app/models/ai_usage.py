from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class AIUsageLog(Base):
    """AI使用记录表"""

    __tablename__ = "ai_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    usage_type = Column(String(50), nullable=False)  # 'generate', 'summarize', 'chat'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
