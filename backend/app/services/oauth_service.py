import httpx
from urllib.parse import urlencode, quote
from app.core.config import settings
from app.core.logger import app_logger as logger


def github_enabled() -> bool:
    return bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET and settings.GITHUB_REDIRECT_URI)


def get_github_authorize_url(state: str = "") -> str:
    if not github_enabled():
        raise RuntimeError("GitHub OAuth 未配置")
    base = "https://github.com/login/oauth/authorize"
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "read:user user:email",
        "state": state,
    }
    query = urlencode(params)
    return f"{base}?{query}"


async def github_get_access_token(code: str) -> str | None:
    if not github_enabled():
        return None
    url = "https://github.com/login/oauth/access_token"
    data = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
    }
    headers = {"Accept": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, data=data, headers=headers)
            resp_json = resp.json()
            return resp_json.get("access_token")
    except Exception as e:
        logger.error(f"GitHub 获取 access_token 失败: {e}")
        return None


async def github_get_user_info(access_token: str) -> dict | None:
    if not access_token:
        return None
    url = "https://api.github.com/user"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                logger.error(f"GitHub 获取用户信息失败: {resp.status_code} {resp.text}")
                return None
            data = resp.json()
            return {
                "id": str(data.get("id")),
                "login": data.get("login"),
                "name": data.get("name") or data.get("login"),
                "email": data.get("email"),
                "avatar_url": data.get("avatar_url"),
            }
    except Exception as e:
        logger.error(f"GitHub 获取用户信息异常: {e}")
        return None


async def github_get_user_emails(access_token: str) -> list[dict] | None:
    if not access_token:
        return None
    url = "https://api.github.com/user/emails"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return None
            return resp.json()
    except Exception as e:
        logger.error(f"GitHub 获取邮箱列表失败: {e}")
        return None
