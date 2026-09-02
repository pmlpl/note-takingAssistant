from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_usage import AIUsageLog


async def log_ai_usage(db: AsyncSession, user_id: int, usage_type: str):
    """记录AI使用"""
    usage_log = AIUsageLog(user_id=user_id, usage_type=usage_type)
    db.add(usage_log)
    await db.commit()


async def get_user_ai_usage_count(db: AsyncSession, user_id: int) -> int:
    """获取用户AI使用次数"""
    result = await db.execute(select(func.count(AIUsageLog.id)).where(AIUsageLog.user_id == user_id))
    return result.scalar() or 0
