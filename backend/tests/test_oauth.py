"""GitHub OAuth 回调逻辑单元测试（mock 外部 GitHub API 与 CRUD 层）。

覆盖回调的核心分支：
- error / 无 code → 跳转登录页并携带错误参数
- token 交换失败 → 跳转登录页
- 新用户（无 oauth 账号、无本地用户）→ 创建账号 + 绑定 + 携带 token 跳转
- 已有 oauth 账号 → 直接登录并携带 token
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.responses import RedirectResponse

from app.api.v1 import oauth


def _fake_db():
    # AsyncMock：db.commit()/db.refresh() 是 async 方法
    return AsyncMock()


class _FakeUser:
    def __init__(self, email: str):
        self.id = 1
        self.email = email
        self.username = None
        self.nickname = email.split("@")[0]
        self.email_verified = False
        self.token_gen = 0
        self.avatar_url = None


@pytest.mark.asyncio
async def test_callback_error_redirects_login():
    resp = await oauth.github_callback(code=None, state=None, error="access_denied", db=_fake_db())
    assert isinstance(resp, RedirectResponse)
    assert "error=github_access_denied" in resp.headers["location"]


@pytest.mark.asyncio
async def test_callback_no_code_redirects_login():
    resp = await oauth.github_callback(code=None, state=None, error=None, db=_fake_db())
    assert "error=github_no_code" in resp.headers["location"]


@pytest.mark.asyncio
async def test_callback_token_exchange_failed():
    with patch("app.api.v1.oauth.github_get_access_token", new=AsyncMock(return_value=None)):
        resp = await oauth.github_callback(code="code_x", state=None, error=None, db=_fake_db())
    assert "error=github_token_failed" in resp.headers["location"]


@pytest.mark.asyncio
async def test_callback_new_user_creates_and_redirects_with_token():
    user_info = {
        "id": 999,
        "login": "octocat",
        "name": "Octo",
        "email": "octo@example.com",
        "avatar_url": "https://avatar",
    }
    with (
        patch("app.api.v1.oauth.github_get_access_token", new=AsyncMock(return_value="tok")),
        patch("app.api.v1.oauth.github_get_user_info", new=AsyncMock(return_value=user_info)),
        patch("app.crud.user.get_oauth_account", new=AsyncMock(return_value=None)),
        patch("app.crud.user.get_user_by_email", new=AsyncMock(return_value=None)),
        patch("app.crud.user.create_user", new=AsyncMock(return_value=_FakeUser("octo@example.com"))),
        patch("app.crud.user.create_oauth_account", new=AsyncMock()),
    ):
        resp = await oauth.github_callback(code="code_x", state=None, error=None, db=_fake_db())
    assert isinstance(resp, RedirectResponse)
    loc = resp.headers["location"]
    assert "token=" in loc and "provider=github" in loc


@pytest.mark.asyncio
async def test_callback_existing_oauth_account_logs_in():
    user_info = {"id": 7, "login": "old", "name": "Old", "email": "old@example.com"}
    existing = MagicMock(user_id=5, provider_username=None, avatar_url=None)
    with (
        patch("app.api.v1.oauth.github_get_access_token", new=AsyncMock(return_value="tok")),
        patch("app.api.v1.oauth.github_get_user_info", new=AsyncMock(return_value=user_info)),
        patch("app.crud.user.get_oauth_account", new=AsyncMock(return_value=existing)),
        patch("app.crud.user.get_user", new=AsyncMock(return_value=_FakeUser("old@example.com"))),
    ):
        resp = await oauth.github_callback(code="code_x", state=None, error=None, db=_fake_db())
    assert "token=" in resp.headers["location"]
