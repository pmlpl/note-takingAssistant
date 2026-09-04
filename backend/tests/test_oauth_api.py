"""app.api.v1.oauth 接口测试

覆盖 GitHub OAuth 配置、授权 URL、邮箱验证码等接口。
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_token(client):
    email = f"oauth_{os.urandom(4).hex()}@example.com"
    password = "OAuth123456"
    client.post("/api/v1/user/register", json={"email": email, "password": password, "nickname": "oauthuser"})
    response = client.post("/api/v1/user/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


# ============== GET /github/config ==============

def test_github_config_public(client):
    response = client.get("/api/v1/oauth/github/config")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert isinstance(data["enabled"], bool)


def test_github_config_disabled(client):
    with patch("app.api.v1.oauth.github_enabled", return_value=False):
        response = client.get("/api/v1/oauth/github/config")
    assert response.status_code == 200
    assert response.json()["enabled"] is False


def test_github_config_enabled(client):
    with patch("app.api.v1.oauth.github_enabled", return_value=True):
        response = client.get("/api/v1/oauth/github/config")
    assert response.status_code == 200
    assert response.json()["enabled"] is True


# ============== POST /github/authorize ==============

def test_github_authorize_disabled(client):
    with patch("app.api.v1.oauth.github_enabled", return_value=False):
        response = client.post("/api/v1/oauth/github/authorize", json={})
    assert response.status_code in (400, 404)


def test_github_authorize_success(client):
    with patch("app.api.v1.oauth.github_enabled", return_value=True), \
         patch("app.api.v1.oauth.get_github_authorize_url", return_value="https://github.com/login/oauth/authorize?client_id=test"):
        response = client.post("/api/v1/oauth/github/authorize", json={"state": "test_state"})
    assert response.status_code == 200
    data = response.json()
    assert "authorize_url" in data or "url" in data


def test_github_authorize_with_state(client):
    with patch("app.api.v1.oauth.github_enabled", return_value=True), \
         patch("app.api.v1.oauth.get_github_authorize_url", return_value="https://github.com/auth?state=mystate"):
        response = client.post("/api/v1/oauth/github/authorize", json={"state": "mystate"})
    assert response.status_code == 200


# ============== GET /github/callback ==============

def test_github_callback_missing_code(client):
    response = client.get("/api/v1/oauth/github/callback", follow_redirects=False)
    assert response.status_code in (302, 307, 400, 422)


def test_github_callback_with_code(client):
    with patch("app.api.v1.oauth.github_get_access_token", new_callable=AsyncMock) as mock_token, \
         patch("app.api.v1.oauth.github_get_user_info", new_callable=AsyncMock) as mock_user:
        mock_token.return_value = "gho_test_token"
        mock_user.return_value = {
            "id": "12345",
            "login": "testuser",
            "name": "Test User",
            "email": "github@example.com",
            "avatar_url": "https://avatar.url",
        }
        response = client.get("/api/v1/oauth/github/callback?code=test_code&state=test_state",
                              follow_redirects=False)
    # 回调重定向到前端
    assert response.status_code in (200, 302, 307, 400)


def test_github_callback_token_failed(client):
    with patch("app.api.v1.oauth.github_get_access_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = None
        response = client.get("/api/v1/oauth/github/callback?code=bad_code", follow_redirects=False)
    assert response.status_code in (302, 307, 400, 401, 500)


# ============== POST /email/send-code ==============

def test_send_email_code_missing_email(client):
    response = client.post("/api/v1/oauth/email/send-code", json={})
    assert response.status_code == 422


def test_send_email_code_invalid_email(client):
    # SendCodeRequest 仅校验 email 为 str，不校验格式；mock 邮件发送成功
    with patch("app.api.v1.oauth.send_verification_code_email", return_value=True):
        response = client.post("/api/v1/oauth/email/send-code", json={"email": "not-an-email"})
    assert response.status_code == 200


def test_send_email_code_success(client):
    with patch("app.api.v1.oauth.send_verification_code_email", return_value=True):
        response = client.post(
            "/api/v1/oauth/email/send-code",
            json={"email": "test@example.com"},
        )
    assert response.status_code == 200


def test_send_email_code_smtp_not_configured(client):
    with patch("app.api.v1.oauth.send_verification_code_email", return_value=False):
        response = client.post(
            "/api/v1/oauth/email/send-code",
            json={"email": "test@example.com"},
        )
    assert response.status_code in (200, 400, 500)


# ============== POST /email/verify ==============

def test_verify_email_code_missing_fields(client):
    response = client.post("/api/v1/oauth/email/verify", json={})
    assert response.status_code == 422


def test_verify_email_code_missing_code(client):
    response = client.post("/api/v1/oauth/email/verify", json={"email": "test@example.com"})
    assert response.status_code == 422


def test_verify_email_code_invalid_code(client):
    # 验证码不存在或错误
    response = client.post(
        "/api/v1/oauth/email/verify",
        json={"email": "test@example.com", "code": "000000"},
    )
    assert response.status_code in (400, 401)


# ============== POST /email/bind-code ==============

def test_send_bind_code_requires_auth(client):
    response = client.post("/api/v1/oauth/email/bind-code", json={"email": "new@example.com"})
    assert response.status_code == 401


def test_send_bind_code_missing_email(client, auth_token):
    response = client.post(
        "/api/v1/oauth/email/bind-code",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={},
    )
    assert response.status_code == 422


def test_send_bind_code_success(client, auth_token):
    with patch("app.api.v1.oauth.send_verification_code_email", return_value=True):
        response = client.post(
            "/api/v1/oauth/email/bind-code",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"email": "newbind@example.com", "action": "bind"},
        )
    assert response.status_code == 200


# ============== POST /email/bind ==============

def test_bind_email_requires_auth(client):
    response = client.post("/api/v1/oauth/email/bind", json={"email": "new@example.com", "code": "123456"})
    assert response.status_code == 401


def test_bind_email_missing_fields(client, auth_token):
    response = client.post(
        "/api/v1/oauth/email/bind",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={},
    )
    assert response.status_code == 422


def test_bind_email_invalid_code(client, auth_token):
    response = client.post(
        "/api/v1/oauth/email/bind",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"email": "newbind@example.com", "code": "000000", "action": "bind"},
    )
    assert response.status_code in (400, 401)


# ============== POST /github/authorize 绑定模式 ==============

def test_github_authorize_with_auth_bind_mode(client, auth_token):
    """已登录用户请求授权 URL，state 应带 bind_ 前缀"""
    with patch("app.api.v1.oauth.github_enabled", return_value=True), \
         patch("app.api.v1.oauth.get_github_authorize_url", return_value="https://github.com/auth?state=bind_test"):
        response = client.post(
            "/api/v1/oauth/github/authorize",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={},
        )
    assert response.status_code == 200
    data = response.json()
    assert "state" in data
    assert data["state"].startswith("bind_")


# ============== GET /github/callback 错误分支 ==============

def test_github_callback_with_error(client):
    response = client.get(
        "/api/v1/oauth/github/callback?error=access_denied",
        follow_redirects=False,
    )
    assert response.status_code in (302, 307)


def test_github_callback_bind_mode_error(client):
    """绑定模式下的错误应跳转到 oauth-callback 页面"""
    response = client.get(
        "/api/v1/oauth/github/callback?error=access_denied&state=bind_teststate",
        follow_redirects=False,
    )
    assert response.status_code in (302, 307)
    # 绑定模式应跳转到 oauth-callback 而非 login
    assert "oauth-callback" in response.headers.get("location", "")


def test_github_callback_bind_mode_no_code(client):
    response = client.get(
        "/api/v1/oauth/github/callback?state=bind_teststate",
        follow_redirects=False,
    )
    assert response.status_code in (302, 307)
    assert "oauth-callback" in response.headers.get("location", "")


# ============== POST /email/verify 成功路径 ==============

def test_verify_email_code_success_new_user(client):
    """验证码正确且用户不存在时，应自动创建用户并返回 token"""
    with patch("app.api.v1.oauth._get_email_code", return_value="123456"), \
         patch("app.api.v1.oauth._delete_email_code"):
        email = f"verify_new_{os.urandom(4).hex()}@example.com"
        response = client.post(
            "/api/v1/oauth/email/verify",
            json={"email": email, "code": "123456"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == email


def test_verify_email_code_success_existing_user(client):
    """验证码正确且用户已存在时，应标记邮箱已验证并返回 token"""
    email = f"verify_exist_{os.urandom(4).hex()}@example.com"
    client.post("/api/v1/user/register", json={"email": email, "password": "Verify123456", "nickname": "verify"})
    with patch("app.api.v1.oauth._get_email_code", return_value="123456"), \
         patch("app.api.v1.oauth._delete_email_code"):
        response = client.post(
            "/api/v1/oauth/email/verify",
            json={"email": email, "code": "123456"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email_verified"] is True


def test_verify_email_code_wrong_code(client):
    with patch("app.api.v1.oauth._get_email_code", return_value="123456"):
        response = client.post(
            "/api/v1/oauth/email/verify",
            json={"email": "wrong@example.com", "code": "000000"},
        )
    assert response.status_code == 400


# ============== POST /email/bind-code 补充分支 ==============

def test_send_bind_code_invalid_action(client, auth_token):
    response = client.post(
        "/api/v1/oauth/email/bind-code",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"email": "new@example.com", "action": "invalid"},
    )
    assert response.status_code == 400


def test_send_bind_code_email_already_used(client, auth_token):
    """请求绑定的邮箱已被其他用户使用时应返回 400"""
    other_email = f"other_{os.urandom(4).hex()}@example.com"
    client.post("/api/v1/user/register", json={"email": other_email, "password": "Other123456", "nickname": "other"})
    response = client.post(
        "/api/v1/oauth/email/bind-code",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"email": other_email, "action": "bind"},
    )
    assert response.status_code == 400


def test_send_bind_code_change_action(client, auth_token):
    with patch("app.api.v1.oauth.send_verification_code_email", return_value=True):
        response = client.post(
            "/api/v1/oauth/email/bind-code",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"email": f"change_{os.urandom(4).hex()}@example.com", "action": "change"},
        )
    assert response.status_code == 200


# ============== POST /email/bind 成功路径 ==============

def test_bind_email_success(client, auth_token):
    """验证码正确时应成功绑定新邮箱"""
    new_email = f"bind_success_{os.urandom(4).hex()}@example.com"
    with patch("app.api.v1.oauth._get_bind_code", return_value="123456"), \
         patch("app.api.v1.oauth._delete_bind_code"):
        response = client.post(
            "/api/v1/oauth/email/bind",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"email": new_email, "code": "123456", "action": "bind"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == new_email
    assert data["email_verified"] is True


def test_bind_email_invalid_action(client, auth_token):
    response = client.post(
        "/api/v1/oauth/email/bind",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"email": "new@example.com", "code": "123456", "action": "invalid"},
    )
    assert response.status_code == 400


def test_bind_email_wrong_code(client, auth_token):
    with patch("app.api.v1.oauth._get_bind_code", return_value="123456"):
        response = client.post(
            "/api/v1/oauth/email/bind",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"email": "new@example.com", "code": "000000", "action": "bind"},
        )
    assert response.status_code == 400
