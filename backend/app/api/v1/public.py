"""公开接口（欢迎页统计等，无需登录）"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.note import NoteDB
from app.models.user import UserDB

router = APIRouter()


@router.get("/welcome-stats", summary="欢迎页平台统计（公开）")
async def welcome_stats(db: AsyncSession = Depends(get_async_db)):
    """注册用户量、笔记总量、近 30 日每日新增笔记（折线图）"""
    user_count_result = await db.execute(select(func.count(UserDB.id)))
    user_count = int(user_count_result.scalar() or 0)

    note_count_result = await db.execute(select(func.count(NoteDB.id)))
    note_count = int(note_count_result.scalar() or 0)

    days = 30
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=days - 1)

    daily_rows = await db.execute(
        select(func.date(NoteDB.created_at).label("day"), func.count(NoteDB.id).label("cnt"))
        .where(func.date(NoteDB.created_at) >= start_date)
        .group_by(func.date(NoteDB.created_at))
        .order_by(func.date(NoteDB.created_at))
    )
    daily_map = {str(row.day): int(row.cnt) for row in daily_rows.all()}

    daily_series = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        key = d.isoformat()
        daily_series.append({"date": key, "count": daily_map.get(key, 0)})

    return {
        "user_count": user_count,
        "note_count": note_count,
        "daily_new_notes": daily_series,
    }
