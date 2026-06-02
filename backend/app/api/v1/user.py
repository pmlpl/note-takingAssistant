from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.models.user import UserCreate, UserLogin, Token, TokenWithUser, UserResponse, LLMSettingsPut, LLMSettingsResponse, ChangePasswordRequest
from app.crud import user as crud_user
from app.core.security import create_access_token, verify_password, get_password_hash, get_current_user, decode_token_without_verify
from app.core.field_crypto import SecretCryptoError, encrypt_secret, decrypt_secret, api_key_last_four
from app.core.redis_client import blacklist_token
from app.utils.openai_compatible_url import normalize_openai_compatible_base_url
from datetime import timedelta, timezone, datetime
from app.core.config import settings
from pydantic import BaseModel
import os
import uuid
from pathlib import Path

router = APIRouter()


@router.post("/register", summary="用户注册", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    """用户注册接口"""
    db_user = await crud_user.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    return await crud_user.create_user(db=db, username=user.username, email=user.email, password=user.password)


@router.post("/login", summary="用户登录", response_model=TokenWithUser)
async def login(user: UserLogin, db: AsyncSession = Depends(get_async_db)):
    """用户登录接口"""
    db_user = await crud_user.authenticate_user(db, username=user.username, password=user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "avatar_url": db_user.avatar_url,
            "created_at": db_user.created_at
        }
    }


@router.post("/logout", summary="用户退出登录（撤销 JWT 令牌）")
async def logout(request: Request):
    """
    退出登录：将当前 JWT 令牌加入 Redis 黑名单。
    令牌在 Redis 中保留至其自然过期时间，到期自动清理。

    调用方式：前端在 Authorization header 中携带 Bearer token，
    就像调用任何需要认证的接口一样。
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少认证令牌")

    token = auth_header[7:]  # 去掉 "Bearer " 前缀

    # 解码令牌获取过期时间（不验证是否过期，我们只关心 exp 字段）
    payload = decode_token_without_verify(token)
    if not payload or "exp" not in payload:
        raise HTTPException(status_code=400, detail="无效的令牌格式")

    # 计算令牌剩余有效秒数
    exp_timestamp = payload["exp"]
    now_timestamp = datetime.now(timezone.utc).timestamp()
    remaining_seconds = int(exp_timestamp - now_timestamp)

    if remaining_seconds <= 0:
        # 令牌本来就过期了，无所谓
        return {"message": "退出成功"}

    # 加入 Redis 黑名单，自动过期
    success = blacklist_token(token, remaining_seconds)
    if not success:
        raise HTTPException(status_code=503, detail="服务暂时不可用，请稍后重试")

    return {"message": "退出成功"}


@router.get("/me", summary="获取当前用户信息", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    """获取当前用户信息（需要JWT认证）"""
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "avatar_url": db_user.avatar_url,
        "created_at": db_user.created_at
    }


@router.get(
    "/me/llm-settings",
    summary="获取当前用户 LLM / BYOK 设置",
    response_model=LLMSettingsResponse,
    response_model_by_alias=True,
)
async def get_llm_settings(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
):
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    last4: str | None = None
    has_key = bool(db_user.llm_api_key_encrypted)
    if has_key and db_user.llm_api_key_encrypted:
        try:
            plain = decrypt_secret(db_user.llm_api_key_encrypted)
            last4 = api_key_last_four(plain)
        except SecretCryptoError:
            raise HTTPException(
                status_code=503,
                detail="无法解密已保存的 API 密钥，请确认服务端加密配置（ENCRYPTION_KEY 或与保存时一致的 SECRET_KEY）未改动",
            ) from None
    return LLMSettingsResponse(
        base_url=normalize_openai_compatible_base_url(db_user.llm_base_url)
        if db_user.llm_base_url
        else None,
        llm_model=db_user.llm_model,
        api_key_last4=last4,
        has_stored_api_key=has_key,
    )


@router.put(
    "/me/llm-settings",
    summary="更新当前用户 LLM / BYOK 设置",
    response_model=LLMSettingsResponse,
    response_model_by_alias=True,
)
async def put_llm_settings(
    body: LLMSettingsPut,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
):
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    stripped_base = body.base_url.strip()
    db_user.llm_base_url = (
        normalize_openai_compatible_base_url(stripped_base) if stripped_base else None
    )
    db_user.llm_model = body.llm_model.strip() or None

    if not body.retain_api_key:
        raw = (body.api_key or "").strip()
        if not raw:
            db_user.llm_api_key_encrypted = None
        else:
            try:
                db_user.llm_api_key_encrypted = encrypt_secret(raw)
            except SecretCryptoError as e:
                raise HTTPException(status_code=503, detail=str(e)) from e

    await db.commit()
    await db.refresh(db_user)

    last4: str | None = None
    has_key = bool(db_user.llm_api_key_encrypted)
    if has_key and db_user.llm_api_key_encrypted:
        try:
            plain = decrypt_secret(db_user.llm_api_key_encrypted)
            last4 = api_key_last_four(plain)
        except SecretCryptoError:
            last4 = None

    return LLMSettingsResponse(
        base_url=normalize_openai_compatible_base_url(db_user.llm_base_url)
        if db_user.llm_base_url
        else None,
        llm_model=db_user.llm_model,
        api_key_last4=last4,
        has_stored_api_key=has_key,
    )


@router.put("/password", summary="修改密码")
async def change_password(req: ChangePasswordRequest, db: AsyncSession = Depends(get_async_db), current_user: dict = Depends(get_current_user)):
    """修改密码接口"""
    if req.newPassword != req.confirmPassword:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")
    
    # 从 JWT token 中获取用户信息
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if not verify_password(req.currentPassword, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="当前密码不正确")
    
    db_user.hashed_password = get_password_hash(req.newPassword)
    await db.commit()
    await db.refresh(db_user)
    
    return {"message": "密码修改成功"}


@router.post("/avatar", summary="上传头像")
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """上传用户头像"""
    # 验证文件类型
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="只支持图片格式（JPG、PNG、GIF、WebP）")
    
    # 验证文件大小（限制5MB）
    file_size = 0
    content = await file.read()
    file_size = len(content)
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过5MB")
    
    # 获取当前用户信息
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 如果用户已有头像，先删除旧文件
    if db_user.avatar_url:
        try:
            # 从URL中提取文件路径
            old_avatar_path = db_user.avatar_url.lstrip('/')
            old_file = Path(old_avatar_path)
            if old_file.exists():
                old_file.unlink()
                print(f"已删除旧头像: {old_avatar_path}")
        except Exception as e:
            print(f"删除旧头像失败: {e}")
            # 不阻断上传流程，继续执行
    
    # 生成唯一文件名
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
    
    upload_dir = Path("uploads/avatars")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存文件
    file_path = upload_dir / unique_filename
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 生成访问URL
    avatar_url = f"/uploads/avatars/{unique_filename}"
    
    # 更新数据库
    db_user.avatar_url = avatar_url
    await db.commit()
    await db.refresh(db_user)
    
    return {"message": "头像上传成功", "avatar_url": avatar_url}


@router.get("/stats", summary="获取用户统计信息")
async def get_user_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取用户统计信息：笔记数量、AI使用次数、活跃天数"""
    from sqlalchemy import select, func, distinct
    from app.models.note import NoteDB
    from app.crud import ai_usage as crud_ai_usage
    from datetime import datetime, timedelta
    
    # 获取用户
    db_user = await crud_user.get_user_by_username(db, username=current_user["username"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user_id = db_user.id
    
    # 统计笔记数量
    note_count_result = await db.execute(
        select(func.count(NoteDB.id)).where(NoteDB.user_id == user_id)
    )
    note_count = note_count_result.scalar() or 0
    
    # 统计AI使用次数
    ai_usage = await crud_ai_usage.get_user_ai_usage_count(db, user_id)
    
    # 计算活跃天数（有笔记创建的日期）
    active_dates_result = await db.execute(
        select(distinct(func.date(NoteDB.created_at))).where(NoteDB.user_id == user_id)
    )
    active_dates = active_dates_result.scalars().all()
    days_active = len(active_dates)
    
    return {
        "note_count": note_count,
        "ai_usage": ai_usage,
        "days_active": days_active
    }