from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.api.v1 import user, note, ai, public
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.startup_migrations import ensure_user_llm_columns
from app.core.config import settings
import os

# 异步初始化数据库表
async def init_db():
    """异步初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 使用 lifespan 替代 on_event
@asynccontextmanager # 这个装饰器用于异步上下文管理，确保在异步操作中正确处理资源释放
async def lifespan(app: FastAPI):
    # 启动时执行
    if os.environ.get("SKIP_APP_LIFESPAN") == "1":
        yield
        return
    await init_db()
    async with AsyncSessionLocal() as session:
        await ensure_user_llm_columns(session)
        await session.commit()
    yield
    # 关闭时执行清理操作
    
    # 关闭数据库连接池
    try:
        await engine.dispose()
    except Exception as e:
        print(f"⚠️ 关闭数据库连接池时出错: {e}")
    
    # 关闭 Redis 连接
    try:
        from app.core.redis_client import redis_client
        if redis_client.is_available():
            redis_client.client.close()
    except Exception as e:
        print(f"⚠️ 关闭 Redis 连接时出错: {e}")

# 初始化FastAPI
app = FastAPI(
    title="AI个人智能笔记助手API",
    description="基于 FastAPI 的 AI 笔记助手后端；AI 能力通过 OpenAI 兼容协议连接 LM Studio（或其它本地推理服务）。",
    version="1.0.0",
    lifespan=lifespan
)

# 跨域配置（必加，否则Vue前端无法访问）
app.add_middleware(
    CORSMiddleware,  # type:ignore
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件服务（用于访问上传的图片）
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
# 注册路由
app.include_router(user.router, prefix="/api/v1/user", tags=["用户管理"])
app.include_router(note.router, prefix="/api/v1/note", tags=["笔记管理"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI智能模块"])
app.include_router(public.router, prefix="/api/v1/public", tags=["公开接口"])

# 测试接口
@app.get("/", tags=["测试"])
def home():
    return {"message": "AI个人智能笔记助手后端运行成功！"}

# 启动服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
