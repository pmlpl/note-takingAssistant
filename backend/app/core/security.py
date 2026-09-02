import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.core.redis_client import is_token_blacklisted

# 定义OAuth2认证方案
# 用于在路由中依赖注入当前用户信息
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, token_gen: int = 0) -> str:
    """创建访问令牌。

    token_gen 是用户级「令牌代数」：改密后服务器会递增该值，让所有旧 token 的 jti 前缀失效。
    jti 格式为: {username}:{token_gen}:{uuid}，便于 Redis 精确撤销单个 token。
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc)
    if expires_delta:
        expire = expire + expires_delta
    else:
        expire = expire + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jti = f"{to_encode.get('sub', 'anon')}:{token_gen}:{uuid.uuid4().hex}"
    to_encode.update({"exp": expire, "jti": jti, "tgen": token_gen})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_jti_from_token(token: str) -> Optional[str]:
    """安全提取 jti（不验证签名），用于 logout 时以 jti 作为黑名单 key。"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False, "verify_signature": False},
        )
        return payload.get("jti")
    except JWTError:
        return None


def get_token_exp_seconds(token: str) -> Optional[int]:
    """估算 token 剩余有效秒数（<=0 表示已过期）。"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False, "verify_signature": False},
        )
        exp = payload.get("exp")
        if not exp:
            return None
        now = datetime.now(timezone.utc).timestamp()
        remaining = int(exp - now)
        return remaining if remaining > 0 else 0
    except JWTError:
        return None


_TGEN_MIN_PREFIX = "tgen_min:"


def _check_tgen_valid(email: str, token_tgen: int, redis_client_ref) -> bool:
    """
    对比用户当前最小有效 tgen 与 token 中携带的 tgen；
    若 Redis 中的 tgen_min > token_tgen，说明此 token 在改密前签发，应拒绝。
    Redis 不可用时返回 True（降级为放行，因为已通过 jti 黑名单兜底）。
    """
    if not redis_client_ref or not redis_client_ref.client:
        return True
    try:
        raw = redis_client_ref.client.get(f"{_TGEN_MIN_PREFIX}{email}")
        if raw is None:
            return True
        min_tgen = int(raw)
        return token_tgen >= min_tgen
    except Exception:
        return True


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """获取当前用户（JWT 认证 + Redis 黑名单 + tgen 代数校验）。"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已失效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_tgen = payload.get("tgen", 0) or 0
        from app.core.redis_client import redis_client as _redis_client_local

        if not _check_tgen_valid(email, token_tgen, _redis_client_local):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="密码已变更，请重新登录",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"email": email}
    except JWTError:
        raise credentials_exception


def decode_token_without_verify(token: str) -> Optional[dict]:
    """
    不验证签名，只解码 JWT 获取 payload。
    用于 logout 时获取令牌剩余有效期。
    """
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False, "verify_signature": False},
        )
    except JWTError:
        return None
