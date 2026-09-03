"""AI 接口测试（mock LLM 流，不发起真实调用）。

覆盖 /api/v1/ai 的生成、总结端点：认证、参数、mock LLM 后的返回契约。
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_token(client):
    email = f"ai_test_{uuid.uuid4().hex[:8]}@example.com"
    password = "Test123456"
    client.post(
        "/api/v1/user/register", json={"email": email, "password": password, "nickname": "aitest"}
    )
    r = client.post("/api/v1/user/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_generate_note_requires_auth(client):
    r = client.post("/api/v1/ai/generate-note", json={"topic": "机器学习"})
    assert r.status_code == 401


def test_generate_note_mocked_llm(client, auth_token, monkeypatch):
    async def fake_stream(*args, **kwargs):
        yield "# 机器学习\n\n这是一篇生成的笔记内容。"

    monkeypatch.setattr("app.api.v1.ai.generate_note_stream", fake_stream)
    r = client.post(
        "/api/v1/ai/generate-note",
        headers=_auth(auth_token),
        json={"topic": "机器学习", "wordCount": 200},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["code"] == 200
    assert "机器学习" in data["data"]["content"]


def test_summarize_note_mocked_llm(client, auth_token, monkeypatch):
    async def fake_analyze(content, *, db_user):
        return {
            "summary": "这是总结",
            "strengths": ["优点1"],
            "weaknesses": [],
            "suggestions": [],
        }

    monkeypatch.setattr("app.api.v1.ai.analyze_note", fake_analyze)
    r = client.post(
        "/api/v1/ai/summarize-note",
        headers=_auth(auth_token),
        json={"content": "这是一篇需要总结的笔记正文内容。"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["code"] == 200
    assert data["data"]["summary"] == "这是总结"
