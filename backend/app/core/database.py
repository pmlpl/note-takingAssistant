from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# 数据库URL
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# 将 mysql+mysqlconnector 转换为 mysql+aiomysql
if SQLALCHEMY_DATABASE_URL.startswith("mysql+mysqlconnector"):
    ASYNC_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "mysql+mysqlconnector", "mysql+aiomysql"
    )
else:
    ASYNC_DATABASE_URL = SQLALCHEMY_DATABASE_URL

# 异步数据库引擎配置
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,  # 连接前检查连接是否有效
    pool_recycle=3600    # 连接回收时间（秒）
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


# 获取异步数据库会话
async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
