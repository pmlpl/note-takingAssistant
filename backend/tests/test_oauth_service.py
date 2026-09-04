"""app.services.oauth_service 测试

通过 mock settings 和 httpx.AsyncClient 来测试 GitHub OAuth 相关函数，
不依赖真实的 GitHub API 调用。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import oauth_service


# ============== github_enabled ==============

def test_github_enabled_false_when_no_config():
    with patch.object(oauth_service.settings, "GITHUB_CLIENT_ID", None), \
         patch.object(oauth_service.settings, "GITHUB_CLIENT_SECRET", None), \
         patch.object(oauth_service.settings, "GITHUB_REDIRECT_URI", None):
        assert oauth_service.github_enabled() is False


def test_github_enabled_true_when_all_config():
    with patch.object(oauth_service.settings, "GITHUB_CLIENT_ID", "client_id"), \
         patch.object(oauth_service.settings, "GITHUB_CLIENT_SECRET", "secret"), \
         patch.object(oauth_service.settings, "GITHUB_REDIRECT_URI", "http://localhost/callback"):
        assert oauth_service.github_enabled() is True


def test_github_enabled_partial_config():
    with patch.object(oauth_service.settings, "GITHUB_CLIENT_ID", "client_id"), \
         patch.object(oauth_service.settings, "GITHUB_CLIENT_SECRET", None), \
         patch.object(oauth_service.settings, "GITHUB_REDIRECT_URI", "http://localhost/callback"):
        assert oauth_service.github_enabled() is False


# ============== get_github_authorize_url ==============

def test_get_github_authorize_url_raises_when_disabled():
    with patch.object(oauth_service, "github_enabled", return_value=False):
        with pytest.raises(RuntimeError, match="GitHub OAuth 未配置"):
            oauth_service.get_github_authorize_url()


def test_get_github_authorize_url_success():
    with patch.object(oauth_service, "github_enabled", return_value=True), \
         patch.object(oauth_service.settings, "GITHUB_CLIENT_ID", "test_client"), \
         patch.object(oauth_service.settings, "GITHUB_REDIRECT_URI", "http://localhost/callback"):
        url = oauth_service.get_github_authorize_url(state="test_state")
        assert "https://github.com/login/oauth/authorize" in url
        assert "client_id=test_client" in url
        assert "redirect_uri=http%3A%2F%2Flocalhost%2Fcallback" in url
        assert "scope=read%3Auser+user%3Aemail" in url
        assert "state=test_state" in url


def test_get_github_authorize_url_empty_state():
    with patch.object(oauth_service, "github_enabled", return_value=True), \
         patch.object(oauth_service.settings, "GITHUB_CLIENT_ID", "test_client"), \
         patch.object(oauth_service.settings, "GITHUB_REDIRECT_URI", "http://localhost/callback"):
        url = oauth_service.get_github_authorize_url()
        assert "state=" in url


# ============== github_get_access_token ==============

@pytest.mark.asyncio
async def test_github_get_access_token_disabled():
    with patch.object(oauth_service, "github_enabled", return_value=False):
        result = await oauth_service.github_get_access_token("code")
        assert result is None


@pytest.mark.asyncio
async def test_github_get_access_token_success():
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "gho_token123", "token_type": "bearer"}

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch.object(oauth_service, "github_enabled", return_value=True), \
         patch.object(oauth_service.settings, "GITHUB_CLIENT_ID", "cid"), \
         patch.object(oauth_service.settings, "GITHUB_CLIENT_SECRET", "sec"), \
         patch.object(oauth_service.settings, "GITHUB_REDIRECT_URI", "http://cb"), \
         patch.object(oauth_service.httpx, "AsyncClient", return_value=mock_client):
        token = await oauth_service.github_get_access_token("test_code")
        assert token == "gho_token123"
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_github_get_access_token_no_token_in_response():
    mock_response = MagicMock()
    mock_response.json.return_value = {"error": "bad_verification_code"}

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch.object(oauth_service, "github_enabled", return_value=True), \
         patch.object(oauth_service.httpx, "AsyncClient", return_value=mock_client):
        token = await oauth_service.github_get_access_token("bad_code")
        assert token is None


@pytest.mark.asyncio
async def test_github_get_access_token_exception():
    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=Exception("Network error"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch.object(oauth_service, "github_enabled", return_value=True), \
         patch.object(oauth_service.httpx, "AsyncClient", return_value=mock_client):
        token = await oauth_service.github_get_access_token("code")
        assert token is None


# ============== github_get_user_info ==============

@pytest.mark.asyncio
async def test_github_get_user_info_empty_token():
    result = await oauth_service.github_get_user_info("")
    assert result is None


@pytest.mark.asyncio
async def test_github_get_user_info_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 12345,
        "login": "testuser",
        "name": "Test User",
        "email": "test@example.com",
        "avatar_url": "https://avatar.url",
    }

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch.object(oauth_service.httpx, "AsyncClient", return_value=mock_client):
        info = await oauth_service.github_get_user_info("valid_token")
        assert info is not None
        assert info["id"] == "12345"
        assert info["login"] == "testuser"
        assert info["name"] == "Test User"
        assert info["email"] == "test@example.com"
        assert info["avatar_url"] == "https://avatar.url"


@pytest.mark.asyncio
async def test_github_get_user_info_name_fallback_to_login():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 1,
        "login": "nonameuser",
        "name": None,
        "email": None,
        "avatar_url": None,
    }

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch.object(oauth_service.httpx, "AsyncClient", return_value=mock_client):
        info = await oauth_service.github_get_user_info("token")
        assert info["name"] == "nonameuser"


@pytest.mark.asyncio
async def test_github_get_user_info_http_error():
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Bad credentials"

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch.object(oauth_service.httpx, "AsyncClient", return_value=mock_client):
        info = await oauth_service.github_get_user_info("bad_token")
        assert info is None


@pytest.mark.asyncio
async def test_github_get_user_info_exception():
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch.object(oauth_service.httpx, "AsyncClient", return_value=mock_client):
        info = await oauth_service.github_get_user_info("token")
        assert info is None


# ============== github_get_user_emails ==============

@pytest.mark.asyncio
async def test_github_get_user_emails_empty_token():
    result = await oauth_service.github_get_user_emails("")
    assert result is None


@pytest.mark.asyncio
async def test_github_get_user_emails_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"email": "primary@example.com", "primary": True, "verified": True},
        {"email": "secondary@example.com", "primary": False, "verified": True},
    ]

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch.object(oauth_service.httpx, "AsyncClient", return_value=mock_client):
        emails = await oauth_service.github_get_user_emails("token")
        assert emails is not None
        assert len(emails) == 2
        assert emails[0]["email"] == "primary@example.com"


@pytest.mark.asyncio
async def test_github_get_user_emails_http_error():
    mock_response = MagicMock()
    mock_response.status_code = 403

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch.object(oauth_service.httpx, "AsyncClient", return_value=mock_client):
        emails = await oauth_service.github_get_user_emails("token")
        assert emails is None


@pytest.mark.asyncio
async def test_github_get_user_emails_exception():
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=Exception("Timeout"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch.object(oauth_service.httpx, "AsyncClient", return_value=mock_client):
        emails = await oauth_service.github_get_user_emails("token")
        assert emails is None
