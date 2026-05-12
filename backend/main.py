from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1 import user, note, ai
from app.core.database import engine, Base
from app.core.config import settings
import os
import asyncio
# 初始化FastAPI
app = FastAPI(
    title="AI个人智能笔记助手API",
    description="基于FastAPI的AI笔记助手后端接口，支持用户管理、笔记管理、AI生成与总结",
    version="1.0.0"
)

# 初始化数据库表（首次运行时创建）

# 异步初始化数据库表
async def init_db():
    """异步初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 在应用启动时初始化数据库
@app.on_event("startup")
async def startup():
    await init_db()

# 跨域配置（必加，否则Vue前端无法访问）
app.add_middleware(
    CORSMiddleware, # type:ignore
    allow_origins=["*"],  # 明确指定前端地址
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

