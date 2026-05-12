from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import UserDB
from app.core.security import get_password_hash


async def get_user(db: AsyncSession, user_id: int):
    """根据ID获取用户"""
    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str):
    """根据用户名获取用户"""
    result = await db.execute(select(UserDB).where(UserDB.username == username))
    return result.scalar_one_or_none()


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    """获取用户列表"""
    result = await db.execute(select(UserDB).offset(skip).limit(limit))
    return result.scalars().all()


async def create_user(db: AsyncSession, username: str, email: str, password: str):
    """创建新用户"""
    hashed_password = get_password_hash(password)
    db_user = UserDB(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def authenticate_user(db: AsyncSession, username: str, password: str):
    """验证用户"""
    user = await get_user_by_username(db, username)
    if not user:
        return False
    from app.core.security import verify_password
    if not verify_password(password, user.hashed_password):
        return False
    return user
