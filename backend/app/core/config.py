from typing import Optional
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # 服务器配置（从 .env 文件读取）
    API_HOST: str
    API_PORT: int
    API_BASE_URL: str
    FRONTEND_URL: str  # 前端地址，用于跨域配置
    
    # 数据库配置（从 .env 文件读取）
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    
    # 自动构建 DATABASE_URL（使用异步驱动 aiomysql）
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Redis配置（从 .env 文件读取）
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: Optional[str] = None

    # JWT配置（从 .env 文件读取）
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # AI配置（从 .env 文件读取）
    LM_STUDIO_URL: str
    LM_STUDIO_MODEL: str
    OPENAI_API_KEY: Optional[str] = None
    ENCRYPTION_KEY: Optional[str] = None
    LLM_HTTP_READ_TIMEOUT_SECONDS: float
    LLM_HTTP_TRUST_ENV: bool

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        env_file_encoding = 'utf-8'
        extra = 'ignore'  # 忽略未定义的字段


settings = Settings()
