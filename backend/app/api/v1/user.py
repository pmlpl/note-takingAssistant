from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.models.user import UserCreate, UserLogin, Token, TokenWithUser, UserResponse, LLMSettingsPut, LLMSettingsResponse, ChangePasswordRequest
from app.crud import user as crud_user
from app.core.security import create_access_token, verify_password, get_password_hash, get_current_user, decode_token_without_verify
from app.core.field_crypto import SecretCryptoError, encrypt_secret, decrypt_secret, api_key_last_four
from app.core.redis_client import blacklist_token
from app.core.rate_limit import rate_limit_anon, rate_limit_user
from app.core.logger import app_logger as logger
from app.utils.openai_compatible_url import (
    normalize_openai_compatible_base_url,
    assert_safe_llm_url,
    UnsafeLlmUrlError,
)
from datetime import timedelta, timezone, datetime
from app.core.config import settings
from pydantic import BaseModel
import os
import re
import uuid
from pathlib import Path

router = APIRouter()


# ====== 输入校验工具 ======
_NICKNAME_RE = re.compile(r"^[a-zA-Z0-9_\u4e00-\u9fa5][a-zA-Z0-9_\-\u4e00-\u9fa5]{1,31}$")


def _validate_nickname(nickname: str | None) -> None:
    if not nickname:
        return
    if len(nickname) < 2 or len(nickname) > 32:
        raise HTTPException(status_code=400, detail="昵称长度必须在 2-32 之间")
    if not _NICKNAME_RE.match(nickname):
        raise HTTPException(
            status_code=400,
            detail="昵称只能包含字母、数字、中文、下划线、短横线",
        )


def _validate_password(password: str) -> None:
    if not password or len(password) < 8:
        raise HTTPException(status_code=400, detail="密码至少需要 8 个字符")
    if len(password) > 128:
        raise HTTPException(status_code=400, detail="密码过长")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        raise HTTPException(status_code=400, detail="密码必须同时包含字母和数字")


def _validate_email(email: str) -> None:
    if not email:
        raise HTTPException(status_code=400, detail="邮箱不能为空")
    email_re = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
    if not email_re.match(email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")


@router.post("/register", summary="用户注册", response_model=UserResponse)
async def register(
    user: UserCreate,
    db: AsyncSession = Depends(get_async_db),
    _: None = Depends(rate_limit_anon("register")),
):
    """用户注册接口"""
    _validate_email(user.email)
    _validate_password(user.password)
    _validate_nickname(user.nickname)

    db_user_by_email = await crud_user.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=400, detail="该邮箱已被注册")

    nickname = user.nickname or user.email.split("@")[0]

    return await crud_user.create_user(db=db, email=user.email, password=user.password, nickname=nickname)


@router.post("/login", summary="用户登录", response_model=TokenWithUser)
async def login(
    user: UserLogin,
    db: AsyncSession = Depends(get_async_db),
    _: None = Depends(rate_limit_anon("login")),
):
    """用户登录接口"""
    db_user = await crud_user.authenticate_user(db, email=user.email, password=user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    current_tgen = getattr(db_user, "token_gen", 0) or 0
    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=access_token_expires,
        token_gen=current_tgen,
    )

    display_nickname = db_user.nickname or db_user.username or db_user.email.split("@")[0]

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "nickname": display_nickname,
            "username": db_user.username,
            "email": db_user.email,
            "email_verified": bool(db_user.email_verified),
            "avatar_url": db_user.avatar_url,
            "created_at": db_user.created_at
        }
    }


@router.post("/logout", summary="用户退出登录（撤销 JWT 令牌）")
async def logout(
    request: Request,
    _: None = Depends(rate_limit_anon("login")),
):
    """
    退出登录：将当前 JWT 令牌的 jti 加入 Redis 黑名单。
    令牌在 Redis 中保留至其自然过期时间，到期自动清理。
    """
    from app.core.security import get_jti_from_token, get_token_exp_seconds

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少认证令牌")

    token = auth_header[7:]  # 去掉 "Bearer " 前缀

    jti = get_jti_from_token(token)
    remaining = get_token_exp_seconds(token)

    if remaining is None or remaining <= 0:
        # 令牌本来就过期或格式异常，直接返回成功
        return {"message": "退出成功"}

    # 用 jti 作 key 加入黑名单（比整串 token 短得多，且稳定）
    if jti:
        success = blacklist_token(jti, remaining)
    else:
        # 老 token（无 jti）降级为整串 key
        success = blacklist_token(token, remaining)

    if not success:
        raise HTTPException(status_code=503, detail="服务暂时不可用，请稍后重试")

    return {"message": "退出成功"}


@router.get("/me", summary="获取当前用户信息", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    _: None = Depends(rate_limit_user("notes")),
):
    """获取当前用户信息（需要JWT认证）"""
    db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    display_nickname = db_user.nickname or db_user.username or db_user.email.split("@")[0]

    return {
        "id": db_user.id,
        "nickname": display_nickname,
        "username": db_user.username,
        "email": db_user.email,
        "email_verified": bool(db_user.email_verified),
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
    _: None = Depends(rate_limit_user("notes")),
):
    db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
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
    # 再次校验存储的 base_url：防止通过其他渠道写入不安全地址
    normalized_url = None
    if db_user.llm_base_url:
        try:
            assert_safe_llm_url(db_user.llm_base_url)
            normalized_url = normalize_openai_compatible_base_url(db_user.llm_base_url)
        except UnsafeLlmUrlError:
            normalized_url = None  # 不安全则不返回，让用户重新填写
    return LLMSettingsResponse(
        base_url=normalized_url,
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
    _: None = Depends(rate_limit_user("notes")),
):
    db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    stripped_base = body.base_url.strip()
    if stripped_base:
        try:
            assert_safe_llm_url(stripped_base)
        except UnsafeLlmUrlError as e:
            raise HTTPException(status_code=400, detail=str(e)) from None
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
async def change_password(
    req: ChangePasswordRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(rate_limit_user("notes")),
):
    """修改密码接口。改密后所有历史 token 失效（通过 token_gen 递增 + Redis 最小值同步）。"""
    from app.core.redis_client import redis_client
    from app.core.config import settings

    if req.newPassword != req.confirmPassword:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")

    _validate_password(req.newPassword)

    db_user = await crud_user.get_user_by_email(db, email=current_user["email"])

    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not verify_password(req.currentPassword, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="当前密码不正确")

    db_user.hashed_password = get_password_hash(req.newPassword)
    db_user.token_gen = (getattr(db_user, "token_gen", 0) or 0) + 1
    await db.commit()
    await db.refresh(db_user)

    ttl = int(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 * 2)
    try:
        if redis_client.client:
            redis_client.client.setex(
                f"tgen_min:{db_user.email}", ttl, str(db_user.token_gen)
            )
    except Exception as e:
        logger.info(f"⚠️ 同步 tgen_min 失败（不阻断改密成功）: {e}")

    return {"message": "密码修改成功，所有旧登录会话已失效"}


@router.post("/avatar", summary="上传头像")
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(rate_limit_user("notes")),
):
    """上传用户头像（做扩展名 + 魔数双重校验）。"""
    from app.utils.file_upload import validate_image_bytes, safe_image_filename

    content = await file.read()

    # 魔数 + 扩展名校验
    ok, ext, err = validate_image_bytes(content, file.filename or "")
    if not ok:
        raise HTTPException(status_code=400, detail=err)

    db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 如果用户已有头像，先删除旧文件（路径仅保留相对部分，防止 ../ 遍历）
    if db_user.avatar_url:
        try:
            old_avatar_path = db_user.avatar_url.lstrip("/")
            # 只允许删除 uploads/avatars/ 下的文件，避免路径遍历到系统其它位置
            normalized = os.path.normpath(old_avatar_path)
            if normalized.startswith("uploads" + os.sep + "avatars"):
                old_file = Path(normalized)
                if old_file.exists():
                    old_file.unlink()
        except Exception as e:
            logger.info(f"删除旧头像失败: {e}")  # 不阻断上传

    upload_dir = Path("uploads/avatars")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 安全化文件名：使用随机 hex + 标准扩展名
    safe_name = safe_image_filename(file.filename or f"avatar{ext}", ext)
    file_path = upload_dir / safe_name
    with open(file_path, "wb") as f:
        f.write(content)

    # 生成访问 URL
    avatar_url = f"/uploads/avatars/{safe_name}"
    
    # 更新数据库
    db_user.avatar_url = avatar_url
    await db.commit()
    await db.refresh(db_user)
    
    return {"message": "头像上传成功", "avatar_url": avatar_url}


@router.get("/stats", summary="获取用户统计信息")
async def get_user_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(rate_limit_user("notes")),
):
    """获取用户统计信息：笔记数量、AI使用次数、活跃天数"""
    from sqlalchemy import select, func, distinct
    from app.models.note import NoteDB
    from app.crud import ai_usage as crud_ai_usage
    from datetime import datetime, timedelta
    
    db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
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


# ====== 账号绑定 ======

class NicknameUpdate(BaseModel):
    nickname: str


@router.put("/me/nickname", summary="修改昵称")
async def update_nickname(
    body: NicknameUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(rate_limit_user("notes")),
):
    """修改用户昵称"""
    _validate_nickname(body.nickname)

    db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    db_user.nickname = body.nickname
    await db.commit()
    await db.refresh(db_user)

    display_nickname = db_user.nickname or db_user.username or db_user.email.split("@")[0]
    return {"nickname": display_nickname}


@router.get("/me/bindings", summary="获取账号绑定状态")
async def get_bindings(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(rate_limit_user("notes")),
):
    """获取当前用户的账号绑定状态（GitHub、邮箱）"""
    db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 获取所有 OAuth 绑定
    oauth_accounts = await crud_user.get_user_oauth_accounts(db, user_id=db_user.id)

    github_binding = None
    for acc in oauth_accounts:
        if acc.provider == "github":
            github_binding = {
                "provider": "github",
                "openid": acc.openid,
                "provider_username": acc.provider_username,
                "avatar_url": acc.avatar_url,
                "bound_at": acc.created_at.isoformat() if acc.created_at else None,
            }

    return {
        "email": db_user.email,
        "email_verified": bool(db_user.email_verified),
        "has_password": bool(db_user.hashed_password),
        "github": github_binding,
    }


class UnbindEmailRequest(BaseModel):
    password: str


@router.delete("/me/bindings/email", summary="解除邮箱绑定")
async def unbind_email(
    body: UnbindEmailRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(rate_limit_user("notes")),
):
    """解除邮箱绑定（需要验证密码，且必须已有 GitHub 绑定或其他登录方式）"""
    db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not verify_password(body.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="密码不正确")

    # 检查是否有其他登录方式
    oauth_accounts = await crud_user.get_user_oauth_accounts(db, user_id=db_user.id)
    if not oauth_accounts:
        raise HTTPException(status_code=400, detail="没有其他登录方式，无法解除唯一绑定")

    # 解绑邮箱：清除邮箱相关字段（保留其他 OAuth 绑定）
    db_user.email = None
    db_user.email_verified = False
    db_user.hashed_password = None
    await db.commit()

    return {"message": "邮箱已解除绑定"}


@router.delete("/me/bindings/github", summary="解除 GitHub 绑定")
async def unbind_github(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(rate_limit_user("notes")),
):
    """解除 GitHub 绑定（需要保留其他登录方式）"""
    db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查是否有邮箱或其他登录方式
    oauth_accounts = await crud_user.get_user_oauth_accounts(db, user_id=db_user.id)
    github_bound = any(acc.provider == "github" for acc in oauth_accounts)

    if not github_bound:
        raise HTTPException(status_code=400, detail="未绑定 GitHub")

    # 必须保留至少一种登录方式
    remaining_oauth = [acc for acc in oauth_accounts if acc.provider != "github"]
    if not db_user.email and not db_user.hashed_password and not remaining_oauth:
        raise HTTPException(status_code=400, detail="没有其他登录方式，无法解除唯一绑定")

    await crud_user.delete_oauth_account(db, user_id=db_user.id, provider="github")
    await db.commit()

    return {"message": "GitHub 已解除绑定"}