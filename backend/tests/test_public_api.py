"""app.api.v1.public 公开接口测试

测试 welcome-stats 接口，无需认证。
"""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_welcome_stats_returns_200(client):
    response = client.get("/api/v1/public/welcome-stats")
    assert response.status_code == 200


def test_welcome_stats_returns_required_fields(client):
    response = client.get("/api/v1/public/welcome-stats")
    data = response.json()
    assert "user_count" in data
    assert "note_count" in data
    assert "ai_count" in data
    assert "daily_users" in data


def test_welcome_stats_user_count_is_int(client):
    response = client.get("/api/v1/public/welcome-stats")
    data = response.json()
    assert isinstance(data["user_count"], int)
    assert data["user_count"] >= 0


def test_welcome_stats_note_count_is_int(client):
    response = client.get("/api/v1/public/welcome-stats")
    data = response.json()
    assert isinstance(data["note_count"], int)
    assert data["note_count"] >= 0


def test_welcome_stats_ai_count_is_int(client):
    response = client.get("/api/v1/public/welcome-stats")
    data = response.json()
    assert isinstance(data["ai_count"], int)
    assert data["ai_count"] >= 0


def test_welcome_stats_daily_users_is_list(client):
    response = client.get("/api/v1/public/welcome-stats")
    data = response.json()
    assert isinstance(data["daily_users"], list)
    # 应该有 30 天的数据
    assert len(data["daily_users"]) == 30


def test_welcome_stats_daily_users_structure(client):
    response = client.get("/api/v1/public/welcome-stats")
    data = response.json()
    for day in data["daily_users"]:
        assert "date" in day or "day" in day
        assert "new_users" in day
        assert isinstance(day["new_users"], int)


def test_welcome_stats_does_not_require_auth(client):
    # 不带 Authorization header 应该也能访问
    response = client.get("/api/v1/public/welcome-stats")
    assert response.status_code == 200
    assert response.status_code != 401


def test_welcome_stats_consistent_across_calls(client):
    # 连续调用应该返回一致的结构
    r1 = client.get("/api/v1/public/welcome-stats")
    r2 = client.get("/api/v1/public/welcome-stats")
    assert r1.status_code == r2.status_code == 200
    d1 = r1.json()
    d2 = r2.json()
    assert d1["user_count"] == d2["user_count"]
    assert d1["note_count"] == d2["note_count"]
    assert len(d1["daily_users"]) == len(d2["daily_users"])
