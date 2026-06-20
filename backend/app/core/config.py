"""
配置管理。

设计原则：
- 所有字段均带「开发默认值」，本机即使 .env 为空也能启动
- docker-compose 的 environment: 会覆盖这些默认值，实现「一键部署」
- 生产部署只需在 .env 或环境变量中填入真实值即可
"""
from typing import Optional
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # ── 服务器配置 ──────────────────────────
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:8081"   # Docker 前端默认端口

    # ── 数据库配置 ──────────────────────────
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"          # 开发默认值，Docker/生产请在 .env 中覆盖
    DB_NAME: str = "note_db"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # ── Redis 配置 ──────────────────────────
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # ── JWT 配置 ──────────────────────────
    SECRET_KEY: str = "dev-only-insecure-key-replace-in-production!!"  # 务必在生产环境覆盖
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # ── AI / LLM 配置 ──────────────────────────
    LM_STUDIO_URL: str = "http://127.0.0.1:1234/v1"
    LM_STUDIO_MODEL: str = "your-model-id"
    OPENAI_API_KEY: Optional[str] = None
    ENCRYPTION_KEY: Optional[str] = None
    LLM_HTTP_READ_TIMEOUT_SECONDS: float = 1200.0
    LLM_HTTP_TRUST_ENV: bool = False

    # ── 其他 ──────────────────────────
    # 本机调试时设为 true 可开启 uvicorn reload；Docker 中默认为 false（关闭 reload）
    DEBUG: bool = True

    class Config:
        # 同时读取 .env 文件和当前进程环境变量，环境变量优先级更高
        env_file = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"   # 忽略 .env 中未定义的字段


settings = Settings()
