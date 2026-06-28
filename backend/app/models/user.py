from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


# Pydantic模型 - 用于请求/响应
class UserBase(BaseModel):
    nickname: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(UserBase):
    id: int
    username: Optional[str] = None
    email_verified: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenWithUser(Token):
    user: UserResponse


class LLMSettingsResponse(BaseModel):
    """Masked LLM / BYOK settings for GET."""

    model_config = ConfigDict(populate_by_name=True)

    base_url: str | None = Field(default=None, alias="baseUrl")
    llm_model: str | None = Field(default=None, alias="model")
    api_key_last4: str | None = Field(default=None, alias="apiKeyLast4")
    has_stored_api_key: bool = Field(default=False, alias="hasStoredApiKey")


class LLMSettingsPut(BaseModel):
    """Update BYOK fields. retainApiKey=false 时可写入新密钥或留空 apiKey 以清除已存密钥。"""

    model_config = ConfigDict(populate_by_name=True)

    base_url: str = Field(default="", alias="baseUrl")
    llm_model: str = Field(default="", alias="model")
    api_key: str | None = Field(default=None, alias="apiKey")
    retain_api_key: bool = Field(default=True, alias="retainApiKey")


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    currentPassword: str
    newPassword: str
    confirmPassword: str


# SQLAlchemy数据库模型
from sqlalchemy import Column, Integer, String, DateTime, Text, text, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=True)
    nickname = Column(String(50), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    email_verified = Column(Boolean, nullable=False, server_default=text('0'), default=False)
    hashed_password = Column(String(255), nullable=False)
    avatar_url = Column(Text, nullable=True)
    llm_base_url = Column(Text, nullable=True)
    llm_model = Column(String(512), nullable=True)
    llm_api_key_encrypted = Column(Text, nullable=True)
    token_gen = Column(Integer, nullable=False, server_default=text('0'), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OAuthAccountDB(Base):
    __tablename__ = "oauth_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(20), nullable=False, index=True)
    openid = Column(String(128), nullable=False, index=True)
    provider_username = Column(String(128), nullable=True)
    access_token = Column(Text, nullable=True)
    avatar_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
