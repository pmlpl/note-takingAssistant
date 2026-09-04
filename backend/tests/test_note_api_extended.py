"""app.api.v1.note 扩展接口测试

覆盖 search、rag、recent、import 等接口。
"""

import os

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_token(client):
    email = f"note_ext_{os.urandom(4).hex()}@example.com"
    password = "NoteExt123456"
    client.post("/api/v1/user/register", json={"email": email, "password": password, "nickname": "noteuser"})
    response = client.post("/api/v1/user/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_note(client, auth_token, title, content, tags="test", favorite=False):
    response = client.post(
        "/api/v1/note/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": title, "content": content, "tags": tags, "is_favorite": favorite},
    )
    assert response.status_code == 200
    return response.json()


# ============== GET /search ==============

def test_search_requires_auth(client):
    response = client.get("/api/v1/note/search?q=test")
    assert response.status_code == 401


def test_search_by_title(client, auth_token):
    _create_note(client, auth_token, "Python 学习笔记", "<p>Python 内容</p>", tags="python")
    response = client.get(
        "/api/v1/note/search?keyword=Python",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "items" in data
    # 应该能搜到标题含 Python 的笔记
    titles = [n.get("title", "") for n in data["items"]]
    assert any("Python" in t for t in titles)


def test_search_by_content(client, auth_token):
    _create_note(client, auth_token, "测试标题", "<p>这是独特的搜索关键词内容</p>", tags="test")
    response = client.get(
        "/api/v1/note/search?keyword=独特的搜索关键词",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "items" in data


def test_search_empty_query(client, auth_token):
    response = client.get(
        "/api/v1/note/search?keyword=",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code in (200, 400)


def test_search_no_results(client, auth_token):
    response = client.get(
        "/api/v1/note/search?keyword=不存在的关键词xyz123",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "items" in data


def test_search_favorite_filter(client, auth_token):
    _create_note(client, auth_token, "收藏笔记", "<p>内容</p>", tags="fav", favorite=True)
    response = client.get(
        "/api/v1/note/search?keyword=收藏&is_favorite=true",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "items" in data


# ============== GET /recent ==============

def test_recent_notes_requires_auth(client):
    response = client.get("/api/v1/note/recent")
    assert response.status_code == 401


def test_recent_notes_success(client, auth_token):
    _create_note(client, auth_token, "最近笔记1", "<p>内容1</p>")
    _create_note(client, auth_token, "最近笔记2", "<p>内容2</p>")
    response = client.get(
        "/api/v1/note/recent",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ============== GET /{note_id} ==============

def test_get_note_detail_requires_auth(client):
    response = client.get("/api/v1/note/1")
    assert response.status_code == 401


def test_get_note_detail_not_found(client, auth_token):
    response = client.get(
        "/api/v1/note/99999",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 404


def test_get_note_detail_success(client, auth_token):
    note = _create_note(client, auth_token, "详情笔记", "<p>详情内容</p>", tags="detail")
    response = client.get(
        f"/api/v1/note/{note['id']}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == note["id"]
    assert data["title"] == "详情笔记"


# ============== PUT /{note_id} ==============

def test_update_note_requires_auth(client):
    response = client.put("/api/v1/note/1", json={"title": "new"})
    assert response.status_code == 401


def test_update_note_not_found(client, auth_token):
    response = client.put(
        "/api/v1/note/99999",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "new", "content": "<p>new</p>"},
    )
    assert response.status_code == 404


def test_update_note_success(client, auth_token):
    note = _create_note(client, auth_token, "原标题", "<p>原内容</p>", tags="old")
    response = client.put(
        f"/api/v1/note/{note['id']}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "新标题", "content": "<p>新内容</p>", "tags": "new", "is_favorite": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "新标题"
    assert data["is_favorite"] == 1


# ============== DELETE /{note_id} ==============

def test_delete_note_requires_auth(client):
    response = client.delete("/api/v1/note/1")
    assert response.status_code == 401


def test_delete_note_not_found(client, auth_token):
    response = client.delete(
        "/api/v1/note/99999",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 404


def test_delete_note_success(client, auth_token):
    note = _create_note(client, auth_token, "待删除", "<p>内容</p>")
    response = client.delete(
        f"/api/v1/note/{note['id']}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    # 删除后应找不到
    get_response = client.get(
        f"/api/v1/note/{note['id']}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert get_response.status_code == 404


# ============== GET / (笔记列表) ==============

def test_note_list_requires_auth(client):
    response = client.get("/api/v1/note/")
    assert response.status_code == 401


def test_note_list_success(client, auth_token):
    _create_note(client, auth_token, "列表笔记1", "<p>内容1</p>")
    _create_note(client, auth_token, "列表笔记2", "<p>内容2</p>")
    response = client.get(
        "/api/v1/note/",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_note_list_pagination(client, auth_token):
    for i in range(5):
        _create_note(client, auth_token, f"分页笔记{i}", "<p>内容</p>")
    response = client.get(
        "/api/v1/note/?page=1&page_size=2",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ============== POST / (创建笔记) ==============

def test_create_note_requires_auth(client):
    response = client.post("/api/v1/note/", json={"title": "test", "content": "<p>test</p>"})
    assert response.status_code == 401


def test_create_note_missing_title(client, auth_token):
    response = client.post(
        "/api/v1/note/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"content": "<p>no title</p>"},
    )
    assert response.status_code == 422


def test_create_note_with_favorite(client, auth_token):
    response = client.post(
        "/api/v1/note/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "收藏笔记", "content": "<p>内容</p>", "tags": "fav", "is_favorite": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_favorite"] == 1


# ============== RAG 接口 ==============

def test_rag_context_requires_auth(client):
    response = client.get("/api/v1/note/rag/context?query=test")
    assert response.status_code == 401


def test_rag_rebuild_requires_auth(client):
    response = client.post("/api/v1/note/rag/rebuild")
    assert response.status_code == 401


def test_rag_rebuild_success(client, auth_token):
    response = client.post(
        "/api/v1/note/rag/rebuild",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200


def test_rag_context_success(client, auth_token):
    _create_note(client, auth_token, "RAG测试笔记", "<p>RAG测试内容</p>", tags="rag")
    # 先重建索引
    client.post("/api/v1/note/rag/rebuild", headers={"Authorization": f"Bearer {auth_token}"})
    response = client.get(
        "/api/v1/note/rag/context?query=RAG测试",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
