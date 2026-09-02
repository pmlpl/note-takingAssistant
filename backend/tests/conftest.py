"""Pytest 全局配置与异步数据库 fixtures。"""

import asyncio
import os

import pytest
import pytest_asyncio
from cryptography.fernet import Fernet

# 注意：测试中不设置 SKIP_APP_LIFESPAN，让 TestClient(app) 的 with 上下文触发 lifespan，
# lifespan 会调用 init_db() 自动创建所有表（用全局 engine，避免事件循环冲突）
# 测试环境禁用速率限制，避免 CI 单 IP 触发 429
os.environ.setdefault("RATE_LIMIT_DISABLED", "1")
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


@pytest.fixture(autouse=True)
def event_loop():
    """每个测试用独立的事件循环，避免 'Event loop is closed' 错误"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_db_session():
    """提供异步数据库会话，测试结束后回滚所有变更"""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings

    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        tx = await session.begin()
        try:
            yield session
        finally:
            # 仅当事务仍处于活跃状态才回滚（避免 ResourceClosedError）
            if tx.is_active:
                await tx.rollback()

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_user_id(async_db_session):
    """创建测试用户并返回 user_id（使用随机 email 避免并行测试冲突）"""
    from app.core.security import get_password_hash
    from app.models.user import UserDB

    random_suffix = os.urandom(4).hex()
    user = UserDB(
        username=f"testuser_{random_suffix}",
        email=f"test_{random_suffix}@example.com",
        hashed_password=get_password_hash("test123"),
    )
    async_db_session.add(user)
    await async_db_session.flush()
    await async_db_session.refresh(user)
    return user.id
