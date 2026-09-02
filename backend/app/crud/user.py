from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import OAuthAccountDB, UserDB


async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(UserDB).where(UserDB.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(UserDB).where(UserDB.email == email))
    return result.scalar_one_or_none()


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(UserDB).offset(skip).limit(limit))
    return result.scalars().all()


async def create_user(db: AsyncSession, email: str, password: str, nickname: str = None, username: str = None):
    hashed_password = get_password_hash(password)
    db_user = UserDB(email=email, nickname=nickname, username=username, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def authenticate_user(db: AsyncSession, email: str, password: str):
    user = await get_user_by_email(db, email)
    if not user:
        return False
    from app.core.security import verify_password

    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_oauth_account(db: AsyncSession, provider: str, openid: str):
    result = await db.execute(
        select(OAuthAccountDB).where(OAuthAccountDB.provider == provider, OAuthAccountDB.openid == openid)
    )
    return result.scalar_one_or_none()


async def create_oauth_account(
    db: AsyncSession,
    user_id: int,
    provider: str,
    openid: str,
    access_token: str = None,
    avatar_url: str = None,
    provider_username: str = None,
):
    db_oauth = OAuthAccountDB(
        user_id=user_id,
        provider=provider,
        openid=openid,
        provider_username=provider_username,
        access_token=access_token,
        avatar_url=avatar_url,
    )
    db.add(db_oauth)
    await db.commit()
    await db.refresh(db_oauth)
    return db_oauth


async def get_user_oauth_accounts(db: AsyncSession, user_id: int):
    result = await db.execute(select(OAuthAccountDB).where(OAuthAccountDB.user_id == user_id))
    return result.scalars().all()


async def get_user_oauth_by_provider(db: AsyncSession, user_id: int, provider: str):
    result = await db.execute(
        select(OAuthAccountDB).where(OAuthAccountDB.user_id == user_id, OAuthAccountDB.provider == provider)
    )
    return result.scalar_one_or_none()


async def delete_oauth_account(db: AsyncSession, user_id: int, provider: str):
    result = await db.execute(
        select(OAuthAccountDB).where(OAuthAccountDB.user_id == user_id, OAuthAccountDB.provider == provider)
    )
    oauth_account = result.scalar_one_or_none()
    if oauth_account:
        await db.delete(oauth_account)
        await db.commit()
    return oauth_account
