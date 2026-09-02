import random
import secrets
import string
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_db
from app.core.logger import app_logger as logger
from app.core.rate_limit import rate_limit_anon
from app.core.security import create_access_token, get_current_user
from app.crud import user as crud_user
from app.services.email_service import send_verification_code_email
from app.services.oauth_service import (
    get_github_authorize_url,
    github_enabled,
    github_get_access_token,
    github_get_user_emails,
    github_get_user_info,
)

router = APIRouter()


def get_current_user_optional(request: Request):
    """可选的当前用户：有 token 就解析，没有就返回 None"""
    from jose import JWTError, jwt

    from app.core.config import settings

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not email:
            return None
        return {"email": email}
    except JWTError:
        return None


# ==================== GitHub OAuth ====================


class GithubAuthorizeResponse(BaseModel):
    authorize_url: str
    enabled: bool


@router.get("/github/config", summary="获取 GitHub 登录配置")
async def github_config():
    return {"enabled": github_enabled()}


@router.post("/github/authorize", summary="获取 GitHub 授权 URL")
async def github_authorize(
    current_user: dict | None = Depends(get_current_user_optional),
):
    if not github_enabled():
        raise HTTPException(status_code=400, detail="GitHub 登录未配置")
    state = secrets.token_urlsafe(16)

    # 如果已登录，生成绑定模式的 state（bind_前缀），并在 Redis 中记录用户信息
    if current_user:
        from app.core.redis_client import redis_client

        try:
            if redis_client.client:
                redis_client.client.setex(f"github_bind:{state}", 600, current_user["email"])
        except Exception as e:
            logger.warning(f"Redis 存储 GitHub 绑定状态失败: {e}")
        state = f"bind_{state}"

    url = get_github_authorize_url(state=state)
    return {"authorize_url": url, "state": state}


@router.get("/github/callback", summary="GitHub OAuth 回调")
async def github_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    db: AsyncSession = Depends(get_async_db),
):
    # 判断是否为绑定模式
    is_bind_mode = state and state.startswith("bind_")
    bind_state = state[5:] if is_bind_mode else state

    if error:
        if is_bind_mode:
            return _bind_redirect(error=f"github_{error}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=github_{error}")

    if not code:
        if is_bind_mode:
            return _bind_redirect(error="github_no_code")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=github_no_code")

    access_token = await github_get_access_token(code)
    if not access_token:
        if is_bind_mode:
            return _bind_redirect(error="github_token_failed")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=github_token_failed")

    user_info = await github_get_user_info(access_token)
    if not user_info:
        if is_bind_mode:
            return _bind_redirect(error="github_user_failed")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=github_user_failed")

    github_id = user_info["id"]
    github_login = user_info["login"]
    github_name = user_info.get("name") or github_login
    avatar_url = user_info.get("avatar_url")

    email = user_info.get("email")
    if not email:
        emails = await github_get_user_emails(access_token)
        if emails:
            primary_email = next((e for e in emails if e.get("primary") and e.get("verified")), None)
            if primary_email:
                email = primary_email.get("email")

    # ===== 绑定模式 =====
    if is_bind_mode:
        from app.core.redis_client import redis_client

        # 从 Redis 取出绑定用户
        bind_email = None
        try:
            if redis_client.client:
                raw = redis_client.client.get(f"github_bind:{bind_state}")
                if raw:
                    bind_email = raw.decode("utf-8") if isinstance(raw, bytes) else raw
                redis_client.client.delete(f"github_bind:{bind_state}")
        except Exception as e:
            logger.warning(f"Redis 读取 GitHub 绑定状态失败: {e}")

        if not bind_email:
            return _bind_redirect(error="bind_state_expired")

        # 查找当前用户
        db_user = await crud_user.get_user_by_email(db, email=bind_email)
        if not db_user:
            return _bind_redirect(error="user_not_found")

        # 检查这个 GitHub 账号是否已被其他用户绑定
        existing_oauth = await crud_user.get_oauth_account(db, provider="github", openid=github_id)
        if existing_oauth and existing_oauth.user_id != db_user.id:
            return _bind_redirect(error="github_already_bound_to_other")

        # 如果当前用户还没绑定，就创建绑定
        existing_user_oauth = await crud_user.get_user_oauth_by_provider(db, user_id=db_user.id, provider="github")
        if not existing_user_oauth:
            await crud_user.create_oauth_account(
                db,
                user_id=db_user.id,
                provider="github",
                openid=github_id,
                access_token=access_token,
                avatar_url=avatar_url,
                provider_username=github_login,
            )
        else:
            # 已绑定则顺便更新用户名和头像（补全旧数据）
            need_update = False
            if not existing_user_oauth.provider_username and github_login:
                existing_user_oauth.provider_username = github_login
                need_update = True
            if not existing_user_oauth.avatar_url and avatar_url:
                existing_user_oauth.avatar_url = avatar_url
                need_update = True
            if need_update:
                await db.commit()

        return _bind_redirect(success="1")

    # ===== 登录/注册模式（原有逻辑） =====
    oauth_account = await crud_user.get_oauth_account(db, provider="github", openid=github_id)

    if oauth_account:
        db_user = await crud_user.get_user(db, user_id=oauth_account.user_id)
        if not db_user:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=github_user_not_found")
        # 自动补全旧数据：如果已有绑定但缺少用户名或头像，更新一下
        need_update = False
        if not oauth_account.provider_username and github_login:
            oauth_account.provider_username = github_login
            need_update = True
        if not oauth_account.avatar_url and avatar_url:
            oauth_account.avatar_url = avatar_url
            need_update = True
        if need_update:
            await db.commit()
    else:
        if email:
            db_user = await crud_user.get_user_by_email(db, email=email)
            if db_user:
                await crud_user.create_oauth_account(
                    db,
                    user_id=db_user.id,
                    provider="github",
                    openid=github_id,
                    access_token=access_token,
                    avatar_url=avatar_url,
                    provider_username=github_login,
                )
            else:
                db_user = await crud_user.create_user(
                    db=db,
                    email=email,
                    password=secrets.token_urlsafe(24),
                    nickname=github_name,
                )
                db_user.email_verified = True
                await db.commit()
                await db.refresh(db_user)
                await crud_user.create_oauth_account(
                    db,
                    user_id=db_user.id,
                    provider="github",
                    openid=github_id,
                    access_token=access_token,
                    avatar_url=avatar_url,
                    provider_username=github_login,
                )
        else:
            fake_email = f"github_{github_id}@users.noreply.github.com"
            db_user = await crud_user.create_user(
                db=db,
                email=fake_email,
                password=secrets.token_urlsafe(24),
                nickname=github_name,
            )
            await crud_user.create_oauth_account(
                db,
                user_id=db_user.id,
                provider="github",
                openid=github_id,
                access_token=access_token,
                avatar_url=avatar_url,
                provider_username=github_login,
            )

    if not db_user.email:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=github_no_email")

    current_tgen = getattr(db_user, "token_gen", 0) or 0
    access_token_jwt = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_gen=current_tgen,
    )

    redirect_url = f"{settings.FRONTEND_URL}/login?token={access_token_jwt}&provider=github"
    return RedirectResponse(url=redirect_url)


def _bind_redirect(success: str = None, error: str = None):
    """绑定模式下的跳转：跳转到前端 oauth-callback 页面，通过 postMessage 通知父窗口"""
    params = []
    if success:
        params.append(f"success={success}")
    if error:
        params.append(f"error={error}")
    query = "&".join(params)
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/oauth-callback?{query}")


# ==================== 邮箱验证码 ====================


class SendCodeRequest(BaseModel):
    email: str


class VerifyCodeRequest(BaseModel):
    email: str
    code: str


EMAIL_CODE_PREFIX = "email_code:"
EMAIL_CODE_TTL = 300

_dev_email_codes = {}


def _generate_code() -> str:
    return "".join(random.choices(string.digits, k=6))


def _save_email_code(email: str, code: str) -> None:
    from app.core.redis_client import redis_client

    try:
        if redis_client.client:
            redis_client.client.setex(f"{EMAIL_CODE_PREFIX}{email}", EMAIL_CODE_TTL, code)
            return
    except Exception as e:
        logger.warning(f"Redis 存储验证码失败，降级到内存存储: {e}")

    _dev_email_codes[email] = code


def _get_email_code(email: str) -> str | None:
    from app.core.redis_client import redis_client

    try:
        if redis_client.client:
            stored = redis_client.client.get(f"{EMAIL_CODE_PREFIX}{email}")
            if stored:
                return stored.decode("utf-8") if isinstance(stored, bytes) else stored
    except Exception as e:
        logger.warning(f"Redis 读取验证码失败，降级到内存读取: {e}")

    return _dev_email_codes.get(email)


def _delete_email_code(email: str) -> None:
    from app.core.redis_client import redis_client

    try:
        if redis_client.client:
            redis_client.client.delete(f"{EMAIL_CODE_PREFIX}{email}")
    except Exception:
        pass

    _dev_email_codes.pop(email, None)


@router.post("/email/send-code", summary="发送邮箱验证码")
async def send_email_code(
    req: SendCodeRequest,
    _: None = Depends(rate_limit_anon("email_code")),
):
    email = req.email.strip().lower()

    if not email:
        raise HTTPException(status_code=400, detail="邮箱不能为空")

    code = _generate_code()

    has_smtp = bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)

    if has_smtp:
        ok = send_verification_code_email(email, code)
        if not ok:
            raise HTTPException(status_code=500, detail="验证码发送失败，请稍后重试")
    else:
        if not settings.DEBUG:
            raise HTTPException(status_code=503, detail="邮件服务暂不可用")
        logger.info(f"[DEV MODE] 邮箱验证码: email={email}, code={code} (有效期 {EMAIL_CODE_TTL} 秒)")

    _save_email_code(email, code)

    return {"message": "验证码已发送，请注意查收", "expires_in": EMAIL_CODE_TTL}


@router.post("/email/verify", summary="验证邮箱验证码并登录/注册")
async def verify_email_code(
    req: VerifyCodeRequest,
    db: AsyncSession = Depends(get_async_db),
    _: None = Depends(rate_limit_anon("email_verify")),
):
    email = req.email.strip().lower()
    code = req.code.strip()

    if not email or not code:
        raise HTTPException(status_code=400, detail="邮箱和验证码不能为空")

    stored_code = _get_email_code(email)

    if not stored_code:
        raise HTTPException(status_code=400, detail="验证码已过期或不存在")

    if stored_code != code:
        raise HTTPException(status_code=400, detail="验证码错误")

    _delete_email_code(email)

    db_user = await crud_user.get_user_by_email(db, email=email)

    if not db_user:
        nickname = email.split("@")[0]
        db_user = await crud_user.create_user(
            db=db,
            email=email,
            password=secrets.token_urlsafe(24),
            nickname=nickname,
        )

    if not db_user.email_verified:
        db_user.email_verified = True
        await db.commit()
        await db.refresh(db_user)

    current_tgen = getattr(db_user, "token_gen", 0) or 0
    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_gen=current_tgen,
    )

    display_nickname = db_user.nickname or db_user.username or email.split("@")[0]

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
            "created_at": db_user.created_at,
        },
    }


# ==================== 账号绑定相关 ====================


class BindCodeRequest(BaseModel):
    email: str
    action: str  # "bind" 或 "change"


class BindEmailRequest(BaseModel):
    email: str
    code: str
    action: str  # "bind" 或 "change"


BIND_CODE_PREFIX = "bind_code:"
BIND_CODE_TTL = 600  # 10分钟

_dev_bind_codes = {}


def _save_bind_code(key: str, code: str) -> None:
    from app.core.redis_client import redis_client

    try:
        if redis_client.client:
            redis_client.client.setex(key, BIND_CODE_TTL, code)
            return
    except Exception as e:
        logger.warning(f"Redis 存储绑定验证码失败，降级到内存存储: {e}")

    _dev_bind_codes[key] = code


def _get_bind_code(key: str) -> str | None:
    from app.core.redis_client import redis_client

    try:
        if redis_client.client:
            stored = redis_client.client.get(key)
            if stored:
                return stored.decode("utf-8") if isinstance(stored, bytes) else stored
    except Exception as e:
        logger.warning(f"Redis 读取绑定验证码失败，降级到内存读取: {e}")

    return _dev_bind_codes.get(key)


def _delete_bind_code(key: str) -> None:
    from app.core.redis_client import redis_client

    try:
        if redis_client.client:
            redis_client.client.delete(key)
    except Exception:
        pass

    _dev_bind_codes.pop(key, None)


@router.post("/email/bind-code", summary="发送邮箱绑定/换绑验证码")
async def send_bind_code(
    req: BindCodeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    _: None = Depends(rate_limit_anon("email_code")),
):
    """已登录用户绑定新邮箱或换绑邮箱时发送验证码"""
    email = req.email.strip().lower()
    action = req.action  # "bind" 或 "change"

    if not email:
        raise HTTPException(status_code=400, detail="邮箱不能为空")

    if action not in ("bind", "change"):
        raise HTTPException(status_code=400, detail="无效的操作类型")

    # 检查邮箱是否已被其他用户使用
    existing_user = await crud_user.get_user_by_email(db, email=email)
    if existing_user:
        raise HTTPException(status_code=400, detail="该邮箱已被其他账号绑定")

    code = _generate_code()
    key = f"{BIND_CODE_PREFIX}{action}:{email}"

    has_smtp = bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)

    if has_smtp:
        ok = send_verification_code_email(email, code)
        if not ok:
            raise HTTPException(status_code=500, detail="验证码发送失败，请稍后重试")
    else:
        if not settings.DEBUG:
            raise HTTPException(status_code=503, detail="邮件服务暂不可用")
        logger.info(
            f"[DEV MODE] 邮箱绑定验证码: email={email}, action={action}, code={code} (有效期 {BIND_CODE_TTL} 秒)"
        )

    _save_bind_code(key, code)

    return {"message": "验证码已发送，请注意查收", "expires_in": BIND_CODE_TTL}


@router.post("/email/bind", summary="验证邮箱验证码并绑定/换绑邮箱")
async def bind_email(
    req: BindEmailRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    _: None = Depends(rate_limit_anon("email_verify")),
):
    """已登录用户验证邮箱验证码，完成绑定或换绑"""
    email = req.email.strip().lower()
    code = req.code.strip()
    action = req.action  # "bind" 或 "change"

    if not email or not code:
        raise HTTPException(status_code=400, detail="邮箱和验证码不能为空")

    if action not in ("bind", "change"):
        raise HTTPException(status_code=400, detail="无效的操作类型")

    key = f"{BIND_CODE_PREFIX}{action}:{email}"
    stored_code = _get_bind_code(key)

    if not stored_code:
        raise HTTPException(status_code=400, detail="验证码已过期或不存在")

    if stored_code != code:
        raise HTTPException(status_code=400, detail="验证码错误")

    # 删除验证码
    _delete_bind_code(key)

    db_user = await crud_user.get_user_by_email(db, email=current_user["email"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 如果是换绑，先检查新邮箱是否已被使用
    if action == "change":
        existing = await crud_user.get_user_by_email(db, email=email)
        if existing and existing.id != db_user.id:
            raise HTTPException(status_code=400, detail="该邮箱已被其他账号绑定")

    # 更新邮箱
    db_user.email = email
    db_user.email_verified = True
    await db.commit()
    await db.refresh(db_user)

    return {
        "message": "邮箱绑定成功",
        "email": db_user.email,
        "email_verified": bool(db_user.email_verified),
    }
