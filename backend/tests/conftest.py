"""Pytest 全局配置与异步数据库 fixtures。"""
import os
import pytest
import pytest_asyncio
from cryptography.fernet import Fernet

os.environ.setdefault("SKIP_APP_LIFESPAN", "1")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_USER", "root")
os.environ.setdefault("DB_PASSWORD", "note_db_password")
os.environ.setdefault("DB_NAME", "note_db")
os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-characters!!")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("LM_STUDIO_URL", "http://localhost:1234/v1")
os.environ.setdefault("LM_STUDIO_MODEL", "test-model")
os.environ.setdefault("LLM_HTTP_READ_TIMEOUT_SECONDS", "30.0")
os.environ.setdefault("LLM_HTTP_TRUST_ENV", "false")
os.environ.setdefault("REDIS_HOST", "127.0.0.1")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
os.environ.setdefault("API_HOST", "0.0.0.0")
os.environ.setdefault("API_PORT", "8000")
os.environ.setdefault("API_BASE_URL", "http://localhost:8000")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5174")


@pytest_asyncio.fixture
async def async_db_session():
    """提供异步数据库会话，测试结束后回滚所有变更"""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        from app.models.note import NoteDB
        from app.models.user import UserDB
        from app.models.ai_usage import AIUsageLog
        from app.models.note import Base as NoteBase
        from app.models.user import Base as UserBase
        from app.models.ai_usage import Base as AIBase
        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(NoteBase.metadata.create_all)
        await conn.run_sync(AIBase.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        tx = await session.begin()
        yield session
        await tx.rollback()

    await engine.dispose()


@pytest_asyncio.fixture
async def test_user_id(async_db_session):
    """创建测试用户并返回 user_id"""
    from app.core.security import get_password_hash
    from app.models.user import UserDB

    user = UserDB(
        username=f"testuser_{os.urandom(4).hex()}",
        email="test@example.com",
        hashed_password=get_password_hash("test123"),
    )
    async_db_session.add(user)
    await async_db_session.flush()
    await async_db_session.refresh(user)
    return user.id
