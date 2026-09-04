"""app.api.v1.ai 接口测试（补充覆盖）

覆盖流式接口成功路径、对话详情/重命名等 test_ai_api_extended.py 未覆盖的路径。
"""

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


def _async_gen(items):
    """将列表转为异步生成器，用于 mock 流式函数。"""
    async def _gen(**kwargs):
        for item in items:
            yield item
    return _gen


def _async_gen_positional(items):
    """接受位置参数的异步生成器（用于 translate_note_stream 等）。"""
    async def _gen(*args, **kwargs):
        for item in items:
            yield item
    return _gen


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_token(client):
    email = f"ai_api_{os.urandom(4).hex()}@example.com"
    password = "AiApi123456"
    client.post("/api/v1/user/register", json={"email": email, "password": password, "nickname": "aiapi"})
    response = client.post("/api/v1/user/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


# ============== POST /generate-note-stream 成功路径 ==============

def test_generate_note_stream_success(client, auth_token):
    with patch("app.api.v1.ai.generate_note_stream", side_effect=_async_gen(["生成的", "流式", "笔记"])):
        response = client.post(
            "/api/v1/ai/generate-note-stream",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"topic": "Python", "keyword": "异步"},
        )
    assert response.status_code == 200
    assert response.text == "生成的流式笔记"


# ============== POST /translate-note-stream 成功路径 ==============

def test_translate_note_stream_success(client, auth_token):
    with patch("app.api.v1.ai.translate_note_stream", side_effect=_async_gen_positional(["Translated ", "text"])):
        response = client.post(
            "/api/v1/ai/translate-note-stream",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "你好世界", "targetLang": "en"},
        )
    assert response.status_code == 200
    assert "Translated" in response.text


# ============== POST /chat-stream 成功路径 ==============

def test_chat_stream_success(client, auth_token):
    with patch("app.api.v1.ai.chat_with_ai_stream", side_effect=_async_gen_positional(["AI ", "回复"])):
        response = client.post(
            "/api/v1/ai/chat-stream",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"message": "你好", "history": []},
        )
    assert response.status_code == 200
    assert "AI" in response.text


# ============== POST /agent-chat-stream 成功路径 ==============

def test_agent_chat_stream_success(client, auth_token):
    """Agent 流式返回 SSE 事件，mock agent_chat_stream 为异步生成器。"""
    async def _agent_gen(*args, **kwargs):
        yield 'data: {"type":"thinking","content":"思考中"}\n\n'
        yield 'data: {"type":"delta","content":"最终回答"}\n\n'
        yield 'data: {"type":"done","conversation_id":1}\n\n'

    with patch("app.api.v1.ai.agent_chat_stream", side_effect=_agent_gen):
        response = client.post(
            "/api/v1/ai/agent-chat-stream",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"message": "帮我搜索笔记", "history": []},
        )
    assert response.status_code == 200
    assert "thinking" in response.text or "delta" in response.text or "done" in response.text


# ============== GET /conversations/{id} 对话详情 ==============

def test_get_conversation_detail_requires_auth(client):
    response = client.get("/api/v1/ai/conversations/1")
    assert response.status_code == 401


def test_get_conversation_detail_not_found(client, auth_token):
    response = client.get(
        "/api/v1/ai/conversations/99999",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 404


def test_get_conversation_detail_success(client, auth_token):
    # 先创建对话
    create_resp = client.post(
        "/api/v1/ai/conversations",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "详情测试对话"},
    )
    conv_id = create_resp.json()["id"]

    response = client.get(
        f"/api/v1/ai/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conv_id
    assert "messages" in data
    assert isinstance(data["messages"], list)


# ============== PATCH /conversations/{id} 重命名对话 ==============

def test_rename_conversation_requires_auth(client):
    response = client.patch("/api/v1/ai/conversations/1", json={"title": "new"})
    assert response.status_code == 401


def test_rename_conversation_empty_title(client, auth_token):
    create_resp = client.post(
        "/api/v1/ai/conversations",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "待重命名"},
    )
    conv_id = create_resp.json()["id"]

    response = client.patch(
        f"/api/v1/ai/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "   "},
    )
    assert response.status_code == 400


def test_rename_conversation_success(client, auth_token):
    create_resp = client.post(
        "/api/v1/ai/conversations",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "旧标题"},
    )
    conv_id = create_resp.json()["id"]

    response = client.patch(
        f"/api/v1/ai/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "新标题"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "新标题"


def test_rename_conversation_not_found(client, auth_token):
    response = client.patch(
        "/api/v1/ai/conversations/99999",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "新标题"},
    )
    assert response.status_code == 404


# ============== POST /summarize-note 补充分支 ==============

def test_summarize_note_with_long_content(client, auth_token):
    mock_result = {"summary": "总结", "strengths": ["优点"], "weaknesses": ["缺点"], "suggestions": ["建议"]}
    with patch("app.api.v1.ai.analyze_note", new_callable=AsyncMock, return_value=mock_result):
        response = client.post(
            "/api/v1/ai/summarize-note",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "很长的笔记内容" * 100},
        )
    assert response.status_code == 200


# ============== POST /chat 补充分支 ==============

def test_chat_with_empty_history(client, auth_token):
    with patch("app.api.v1.ai.chat_with_ai", new_callable=AsyncMock, return_value="回复"):
        response = client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"message": "你好"},
        )
    assert response.status_code == 200
