from typing import Optional
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # 服务器配置
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_BASE_URL: str = f"http://localhost:{API_PORT}"
    
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

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # JWT配置
    SECRET_KEY: str = "your-secret-key-123456"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 登录有效期30天

    # AI配置（本地LM Studio 或其它 OpenAI 兼容端点）
    LM_STUDIO_URL: str = "http://localhost:1234/v1"
    LM_STUDIO_MODEL: str = "qwen3.5-9b-q4_k_m_gguf"
    # 服务端默认 API Key（可选；LM Studio 常不需要，云端兼容服务可填）
    OPENAI_API_KEY: Optional[str] = None
    # Fernet 密钥（urlsafe base64），用于加密用户自带的 API Key；生成：python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ENCRYPTION_KEY: Optional[str] = None
    # 调用本地大模型时，首 token 与整段生成可能很慢；为 httpx 读超时（秒）
    LLM_HTTP_READ_TIMEOUT_SECONDS: float = 1200.0
    # httpx 是否读取系统代理（HTTP_PROXY 等）。默认 false：本地 LM Studio 直连，避免流量进 Privoxy 等导致 500
    LLM_HTTP_TRUST_ENV: bool = False

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        env_file_encoding = 'utf-8'
        extra = 'ignore'  # 忽略未定义的字段


settings = Settings()
