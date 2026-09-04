"""app.api.v1.user 扩展接口测试

覆盖 logout、stats、password、nickname、bindings 等接口。
"""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_token(client):
    email = f"user_ext_{os.urandom(4).hex()}@example.com"
    password = "UserExt123456"
    client.post("/api/v1/user/register", json={"email": email, "password": password, "nickname": "extuser"})
    response = client.post("/api/v1/user/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


# ============== POST /logout ==============

def test_logout_requires_auth(client):
    response = client.post("/api/v1/user/logout")
    assert response.status_code == 401


def test_logout_success(client, auth_token):
    response = client.post("/api/v1/user/logout", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200


def test_logout_token_invalidated(client, auth_token):
    # 登出后 token 应失效（模拟 Redis 黑名单生效）
    client.post("/api/v1/user/logout", headers={"Authorization": f"Bearer {auth_token}"})
    with patch("app.core.security.is_token_blacklisted", return_value=True):
        response = client.get("/api/v1/user/me", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 401


# ============== GET /me ==============

def test_get_me_requires_auth(client):
    response = client.get("/api/v1/user/me")
    assert response.status_code == 401


def test_get_me_success(client, auth_token):
    response = client.get("/api/v1/user/me", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "nickname" in data


# ============== PUT /password ==============

def test_change_password_requires_auth(client):
    response = client.put("/api/v1/user/password", json={"old_password": "old", "new_password": "new"})
    assert response.status_code == 401


def test_change_password_wrong_old(client, auth_token):
    response = client.put(
        "/api/v1/user/password",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"currentPassword": "WrongPassword", "newPassword": "NewPassword123", "confirmPassword": "NewPassword123"},
    )
    assert response.status_code in (400, 401)


def test_change_password_success(client, auth_token):
    response = client.put(
        "/api/v1/user/password",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"currentPassword": "UserExt123456", "newPassword": "NewPassword123", "confirmPassword": "NewPassword123"},
    )
    assert response.status_code == 200


def test_change_password_invalid_new(client, auth_token):
    response = client.put(
        "/api/v1/user/password",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"currentPassword": "UserExt123456", "newPassword": "short", "confirmPassword": "short"},
    )
    assert response.status_code == 400


# ============== PUT /me/nickname ==============

def test_update_nickname_requires_auth(client):
    response = client.put("/api/v1/user/me/nickname", json={"nickname": "new"})
    assert response.status_code == 401


def test_update_nickname_success(client, auth_token):
    response = client.put(
        "/api/v1/user/me/nickname",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"nickname": "NewNickname"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("nickname") == "NewNickname"


def test_update_nickname_empty(client, auth_token):
    response = client.put(
        "/api/v1/user/me/nickname",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"nickname": ""},
    )
    assert response.status_code in (200, 400)


# ============== GET /stats ==============

def test_get_stats_requires_auth(client):
    response = client.get("/api/v1/user/stats")
    assert response.status_code == 401


def test_get_stats_success(client, auth_token):
    response = client.get("/api/v1/user/stats", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200
    data = response.json()
    # 应该包含笔记数量、AI 使用量等统计
    assert isinstance(data, dict)


# ============== GET /me/bindings ==============

def test_get_bindings_requires_auth(client):
    response = client.get("/api/v1/user/me/bindings")
    assert response.status_code == 401


def test_get_bindings_success(client, auth_token):
    response = client.get("/api/v1/user/me/bindings", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # 应该包含邮箱、GitHub 等绑定状态
    assert "email" in data or "github" in data or "email_verified" in data


# ============== DELETE /me/bindings/github ==============

def test_unbind_github_requires_auth(client):
    response = client.delete("/api/v1/user/me/bindings/github")
    assert response.status_code == 401


def test_unbind_github_not_bound(client, auth_token):
    # 没有绑定 GitHub 时解除绑定
    response = client.delete("/api/v1/user/me/bindings/github", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code in (200, 400, 404)


# ============== 注册边界情况 ==============

def test_register_duplicate_email(client):
    email = f"dup_{os.urandom(4).hex()}@example.com"
    client.post("/api/v1/user/register", json={"email": email, "password": "Test123456", "nickname": "u1"})
    response = client.post("/api/v1/user/register", json={"email": email, "password": "Test123456", "nickname": "u2"})
    assert response.status_code == 400


def test_register_invalid_email(client):
    response = client.post("/api/v1/user/register", json={"email": "not-an-email", "password": "Test123456"})
    assert response.status_code == 400


def test_register_short_password(client):
    response = client.post("/api/v1/user/register", json={"email": "short@example.com", "password": "123"})
    assert response.status_code == 400


def test_login_wrong_password(client):
    email = f"login_{os.urandom(4).hex()}@example.com"
    client.post("/api/v1/user/register", json={"email": email, "password": "Correct123", "nickname": "u"})
    response = client.post("/api/v1/user/login", json={"email": email, "password": "WrongPassword"})
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post("/api/v1/user/login", json={"email": "nonexistent@example.com", "password": "password"})
    assert response.status_code == 401
