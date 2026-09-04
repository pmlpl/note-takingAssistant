"""app.api.v1.ai 扩展接口测试

覆盖 AI 生成、总结、翻译、对话等接口的认证和参数验证。
LLM 调用通过 mock service 层来测试。
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
    email = f"ai_ext_{os.urandom(4).hex()}@example.com"
    password = "AiExt123456"
    client.post("/api/v1/user/register", json={"email": email, "password": password, "nickname": "aiuser"})
    response = client.post("/api/v1/user/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


# ============== POST /generate-note ==============

def test_generate_note_requires_auth(client):
    response = client.post("/api/v1/ai/generate-note", json={"topic": "test"})
    assert response.status_code == 401


def test_generate_note_missing_topic(client, auth_token):
    response = client.post(
        "/api/v1/ai/generate-note",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={},
    )
    assert response.status_code == 422


def _async_gen(items):
    """将列表转为异步生成器，用于 mock generate_note_stream 等流式函数。"""
    async def _gen(**kwargs):
        for item in items:
            yield item
    return _gen


def test_generate_note_mocked_llm(client, auth_token):
    with patch("app.api.v1.ai.generate_note_stream", side_effect=_async_gen(["生成的笔记内容"])):
        response = client.post(
            "/api/v1/ai/generate-note",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"topic": "Python", "keyword": "装饰器", "word_count": 500},
        )
    assert response.status_code == 200


def test_generate_note_with_all_params(client, auth_token):
    with patch("app.api.v1.ai.generate_note_stream", side_effect=_async_gen(["完整笔记"])):
        response = client.post(
            "/api/v1/ai/generate-note",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "topic": "机器学习",
                "keyword": "神经网络",
                "word_count": 800,
                "referenceNotes": [],
            },
        )
    assert response.status_code == 200


# ============== POST /summarize-note ==============

def test_summarize_note_requires_auth(client):
    response = client.post("/api/v1/ai/summarize-note", json={"content": "test"})
    assert response.status_code == 401


def test_summarize_note_missing_content(client, auth_token):
    response = client.post(
        "/api/v1/ai/summarize-note",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={},
    )
    assert response.status_code == 422


def test_summarize_note_mocked_llm(client, auth_token):
    mock_result = {"summary": "总结内容", "strengths": [], "weaknesses": [], "suggestions": []}
    with patch("app.api.v1.ai.analyze_note", new_callable=AsyncMock, return_value=mock_result):
        response = client.post(
            "/api/v1/ai/summarize-note",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "这是一篇很长的笔记内容需要总结"},
        )
    assert response.status_code == 200


# ============== POST /chat ==============

def test_chat_requires_auth(client):
    response = client.post("/api/v1/ai/chat", json={"message": "hello"})
    assert response.status_code == 401


def test_chat_missing_message(client, auth_token):
    response = client.post(
        "/api/v1/ai/chat",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={},
    )
    assert response.status_code == 422


def test_chat_mocked_llm(client, auth_token):
    with patch("app.api.v1.ai.chat_with_ai", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "AI回复"
        response = client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"message": "你好", "history": []},
        )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data or "message" in data or isinstance(data, str)


def test_chat_with_history(client, auth_token):
    with patch("app.api.v1.ai.chat_with_ai", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "带历史的回复"
        response = client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "继续",
                "history": [
                    {"role": "user", "content": "你好"},
                    {"role": "assistant", "content": "你好！"},
                ],
            },
        )
    assert response.status_code == 200


# ============== GET /conversations ==============

def test_get_conversations_requires_auth(client):
    response = client.get("/api/v1/ai/conversations")
    assert response.status_code == 401


def test_get_conversations_success(client, auth_token):
    response = client.get(
        "/api/v1/ai/conversations",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ============== POST /conversations ==============

def test_create_conversation_requires_auth(client):
    response = client.post("/api/v1/ai/conversations", json={"title": "test"})
    assert response.status_code == 401


def test_create_conversation_success(client, auth_token):
    response = client.post(
        "/api/v1/ai/conversations",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "新对话"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "新对话"


def test_create_conversation_default_title(client, auth_token):
    response = client.post(
        "/api/v1/ai/conversations",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={},
    )
    assert response.status_code == 200


# ============== DELETE /conversations/{id} ==============

def test_delete_conversation_requires_auth(client):
    response = client.delete("/api/v1/ai/conversations/1")
    assert response.status_code == 401


def test_delete_conversation_not_found(client, auth_token):
    response = client.delete(
        "/api/v1/ai/conversations/99999",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code in (200, 404)


def test_delete_conversation_success(client, auth_token):
    # 先创建对话
    create_resp = client.post(
        "/api/v1/ai/conversations",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "待删除对话"},
    )
    conv_id = create_resp.json()["id"]

    # 删除对话
    delete_resp = client.delete(
        f"/api/v1/ai/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert delete_resp.status_code == 200


# ============== 流式接口认证测试 ==============

def test_generate_note_stream_requires_auth(client):
    response = client.post("/api/v1/ai/generate-note-stream", json={"topic": "test"})
    assert response.status_code == 401


def test_chat_stream_requires_auth(client):
    response = client.post("/api/v1/ai/chat-stream", json={"message": "test"})
    assert response.status_code == 401


def test_translate_note_stream_requires_auth(client):
    response = client.post("/api/v1/ai/translate-note-stream", json={"content": "test", "target_lang": "en"})
    assert response.status_code == 401


def test_agent_chat_stream_requires_auth(client):
    response = client.post("/api/v1/ai/agent-chat-stream", json={"message": "test"})
    assert response.status_code == 401


# ============== 流式接口参数验证 ==============

def test_generate_note_stream_missing_topic(client, auth_token):
    response = client.post(
        "/api/v1/ai/generate-note-stream",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={},
    )
    assert response.status_code == 422


def test_chat_stream_missing_message(client, auth_token):
    response = client.post(
        "/api/v1/ai/chat-stream",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={},
    )
    assert response.status_code == 422


def test_translate_note_stream_missing_content(client, auth_token):
    response = client.post(
        "/api/v1/ai/translate-note-stream",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"target_lang": "en"},
    )
    assert response.status_code == 422


def test_translate_note_stream_missing_target_lang(client, auth_token):
    response = client.post(
        "/api/v1/ai/translate-note-stream",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"content": "你好"},
    )
    assert response.status_code == 422
