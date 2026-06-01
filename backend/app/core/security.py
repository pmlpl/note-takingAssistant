import bcrypt
from datetime import timezone, timedelta, datetime
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.core.redis_client import is_token_blacklisted

# 定义OAuth2认证方案
# 用于在路由中依赖注入当前用户信息
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    # 计算过期时间
    expire = datetime.now(timezone.utc)
    if expires_delta:
        expire = expire + expires_delta  # 使用传入的过期时间
    else:
        expire = expire + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)  # 使用默认过期时间
    to_encode.update({"exp": expire})  # 添加过期时间到数据库
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """获取当前用户（JWT认证 + Redis 黑名单检查）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 第一步：检查令牌是否被撤销（Redis 黑名单）
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已失效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 第二步：解码验证 JWT
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return {"username": username}
    except JWTError as e:
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
            options={"verify_exp": False}  # 即使过期也解码，拿到 exp 字段
        )
    except JWTError:
        return None
