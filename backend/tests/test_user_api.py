"""app.api.v1.user 接口测试（补充覆盖）

覆盖 register/login 成功路径、llm-settings、avatar、unbind email、
昵称/密码校验分支等 test_user_api_extended.py 未覆盖的路径。
"""

import json
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app


# 最小 1x1 PNG（8-bit RGB），用于头像上传测试
_VALID_PNG = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE,
    0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41, 0x54,
    0x78, 0x9C, 0x63, 0xF8, 0xCF, 0xC0, 0x00, 0x00, 0x00, 0x03, 0x00, 0x01,
    0x5C, 0xD6, 0xE4, 0xCA,
    0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
])


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_token(client):
    email = f"user_api_{os.urandom(4).hex()}@example.com"
    password = "UserApi123456"
    client.post("/api/v1/user/register", json={"email": email, "password": password, "nickname": "apiuser"})
    response = client.post("/api/v1/user/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


# ============== POST /register 成功路径 ==============

def test_register_success_with_nickname(client):
    email = f"reg_nick_{os.urandom(4).hex()}@example.com"
    response = client.post(
        "/api/v1/user/register",
        json={"email": email, "password": "Register123", "nickname": "测试昵称"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["email"] == email
    assert data["nickname"] == "测试昵称"


def test_register_success_default_nickname(client):
    """不传 nickname 时，默认使用邮箱 @ 前的部分"""
    email = f"defaultnick_{os.urandom(4).hex()}@example.com"
    response = client.post(
        "/api/v1/user/register",
        json={"email": email, "password": "Register123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nickname"] == email.split("@")[0]


def test_register_password_too_long(client):
    response = client.post(
        "/api/v1/user/register",
        json={"email": "long@example.com", "password": "a" * 129 + "1"},
    )
    assert response.status_code == 400


def test_register_password_no_letter(client):
    response = client.post(
        "/api/v1/user/register",
        json={"email": "noletter@example.com", "password": "12345678"},
    )
    assert response.status_code == 400


def test_register_password_no_digit(client):
    response = client.post(
        "/api/v1/user/register",
        json={"email": "nodigit@example.com", "password": "abcdefgh"},
    )
    assert response.status_code == 400


def test_register_nickname_too_short(client):
    response = client.post(
        "/api/v1/user/register",
        json={"email": "short@example.com", "password": "Test123456", "nickname": "a"},
    )
    assert response.status_code == 400


def test_register_nickname_invalid_chars(client):
    response = client.post(
        "/api/v1/user/register",
        json={"email": "invalid@example.com", "password": "Test123456", "nickname": "昵称@#$"},
    )
    assert response.status_code == 400


# ============== POST /login 成功路径 ==============

def test_login_success_returns_token_and_user(client):
    email = f"login_ok_{os.urandom(4).hex()}@example.com"
    password = "LoginOk123456"
    client.post("/api/v1/user/register", json={"email": email, "password": password, "nickname": "loginuser"})
    response = client.post("/api/v1/user/login", json={"email": email, "password": password})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == email


# ============== GET /me/llm-settings ==============

def test_get_llm_settings_requires_auth(client):
    response = client.get("/api/v1/user/me/llm-settings")
    assert response.status_code == 401


def test_get_llm_settings_success_no_key(client, auth_token):
    response = client.get(
        "/api/v1/user/me/llm-settings",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "hasStoredApiKey" in data or "has_stored_api_key" in data
    has_key = data.get("hasStoredApiKey", data.get("has_stored_api_key", False))
    assert has_key is False


# ============== PUT /me/llm-settings ==============

def test_put_llm_settings_requires_auth(client):
    response = client.put("/api/v1/user/me/llm-settings", json={"baseUrl": "https://api.example.com/v1"})
    assert response.status_code == 401


def test_put_llm_settings_success_base_url_and_model(client, auth_token):
    response = client.put(
        "/api/v1/user/me/llm-settings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"baseUrl": "https://api.openai.com/v1", "model": "gpt-4o"},
    )
    assert response.status_code == 200
    data = response.json()
    base_url = data.get("baseUrl", data.get("base_url"))
    model = data.get("model", data.get("llm_model"))
    assert base_url == "https://api.openai.com/v1"
    assert model == "gpt-4o"


def test_put_llm_settings_with_api_key(client, auth_token):
    response = client.put(
        "/api/v1/user/me/llm-settings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "baseUrl": "https://api.openai.com/v1",
            "model": "gpt-4o",
            "apiKey": "sk-test-1234567890abcdef",
            "retainApiKey": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    has_key = data.get("hasStoredApiKey", data.get("has_stored_api_key", False))
    assert has_key is True
    last4 = data.get("apiKeyLast4", data.get("api_key_last4"))
    assert last4 == "cdef"


def test_put_llm_settings_clear_api_key(client, auth_token):
    # 先设置一个 key
    client.put(
        "/api/v1/user/me/llm-settings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"apiKey": "sk-test-1234567890abcdef", "retainApiKey": False},
    )
    # 再清除
    response = client.put(
        "/api/v1/user/me/llm-settings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"apiKey": "", "retainApiKey": False},
    )
    assert response.status_code == 200
    data = response.json()
    has_key = data.get("hasStoredApiKey", data.get("has_stored_api_key", False))
    assert has_key is False


def test_put_llm_settings_unsafe_scheme(client, auth_token):
    """非 http/https 协议应被拒绝（不受 DEBUG 模式影响）"""
    response = client.put(
        "/api/v1/user/me/llm-settings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"baseUrl": "ftp://example.com/v1"},
    )
    assert response.status_code == 400


# ============== POST /avatar ==============

def test_upload_avatar_requires_auth(client):
    response = client.post("/api/v1/user/avatar", files={"file": ("test.png", _VALID_PNG, "image/png")})
    assert response.status_code == 401


def test_upload_avatar_invalid_file(client, auth_token):
    response = client.post(
        "/api/v1/user/avatar",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("test.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_avatar_success(client, auth_token):
    response = client.post(
        "/api/v1/user/avatar",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("avatar.png", _VALID_PNG, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "avatar_url" in data
    assert data["avatar_url"].startswith("/uploads/avatars/")


# ============== DELETE /me/bindings/email ==============

def test_unbind_email_requires_auth(client):
    response = client.request(
        "DELETE",
        "/api/v1/user/me/bindings/email",
        content=json.dumps({"password": "test"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 401


def test_unbind_email_no_other_login_method(client, auth_token):
    """仅有邮箱+密码登录时，无法解除邮箱绑定"""
    response = client.request(
        "DELETE",
        "/api/v1/user/me/bindings/email",
        headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
        content=json.dumps({"password": "UserApi123456"}),
    )
    assert response.status_code == 400


def test_unbind_email_wrong_password(client, auth_token):
    response = client.request(
        "DELETE",
        "/api/v1/user/me/bindings/email",
        headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
        content=json.dumps({"password": "WrongPassword"}),
    )
    assert response.status_code == 400


# ============== PUT /password 补充分支 ==============

def test_change_password_mismatch(client, auth_token):
    response = client.put(
        "/api/v1/user/password",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"currentPassword": "UserApi123456", "newPassword": "NewPass123", "confirmPassword": "Different123"},
    )
    assert response.status_code == 400


# ============== PUT /me/nickname 补充分支 ==============

def test_update_nickname_too_short(client, auth_token):
    response = client.put(
        "/api/v1/user/me/nickname",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"nickname": "a"},
    )
    assert response.status_code == 400


def test_update_nickname_invalid_chars(client, auth_token):
    response = client.put(
        "/api/v1/user/me/nickname",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"nickname": "昵称@#$%"},
    )
    assert response.status_code == 400
