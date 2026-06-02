"""公开接口（欢迎页统计等，无需登录）"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.user import UserDB
from app.utils.stats_series import build_daily_series

router = APIRouter()

STATS_DAYS = 30


def _today_utc() -> datetime.date:
    return datetime.now(timezone.utc).date()


@router.get("/welcome-stats", summary="欢迎页平台统计（公开）")
async def welcome_stats(db: AsyncSession = Depends(get_async_db)):
    """注册用户总量与近 30 日每日新增注册。"""
    user_count_result = await db.execute(select(func.count(UserDB.id)))
    user_count = int(user_count_result.scalar() or 0)

    today = _today_utc()
    start_date = today - timedelta(days=STATS_DAYS - 1)

    user_rows = await db.execute(
        select(func.date(UserDB.created_at).label("day"), func.count(UserDB.id).label("cnt"))
        .where(func.date(UserDB.created_at) >= start_date)
        .where(func.date(UserDB.created_at) <= today)
        .group_by(func.date(UserDB.created_at))
        .order_by(func.date(UserDB.created_at))
    )
    user_map = {str(row.day): {"new_users": int(row.cnt)} for row in user_rows.all()}
    daily_users = build_daily_series(start_date, STATS_DAYS, user_map, defaults={"new_users": 0})

    return {
        "user_count": user_count,
        "daily_users": daily_users,
    }
