"""app.api.v1.note 接口测试（补充覆盖）

覆盖 upload-image、recent/update、import、重复标题等 test_note_api_extended.py 未覆盖的路径。
"""

import os

import pytest
from fastapi.testclient import TestClient

from main import app


# 最小 1x1 PNG
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
    email = f"note_api_{os.urandom(4).hex()}@example.com"
    password = "NoteApi123456"
    client.post("/api/v1/user/register", json={"email": email, "password": password, "nickname": "noteapi"})
    response = client.post("/api/v1/user/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_note(client, auth_token, title, content="<p>内容</p>", tags="test"):
    response = client.post(
        "/api/v1/note/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": title, "content": content, "tags": tags},
    )
    assert response.status_code == 200
    return response.json()


# ============== POST /upload-image ==============

def test_upload_image_requires_auth(client):
    response = client.post("/api/v1/note/upload-image", files={"file": ("test.png", _VALID_PNG, "image/png")})
    assert response.status_code == 401


def test_upload_image_invalid_file(client, auth_token):
    response = client.post(
        "/api/v1/note/upload-image",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("test.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_image_success(client, auth_token):
    response = client.post(
        "/api/v1/note/upload-image",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("image.png", _VALID_PNG, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert data["url"].startswith("/uploads/images/")


# ============== POST /recent/update ==============

def test_update_recent_order_requires_auth(client):
    response = client.post("/api/v1/note/recent/update", json=[1, 2, 3])
    assert response.status_code == 401


def test_update_recent_order_success(client, auth_token):
    note1 = _create_note(client, auth_token, "最近笔记A")
    note2 = _create_note(client, auth_token, "最近笔记B")
    response = client.post(
        "/api/v1/note/recent/update",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=[note1["id"], note2["id"]],
    )
    assert response.status_code == 200
    data = response.json()
    assert "count" in data


def test_update_recent_order_empty(client, auth_token):
    response = client.post(
        "/api/v1/note/recent/update",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=[],
    )
    assert response.status_code == 200


# ============== POST /import ==============

def test_import_note_requires_auth(client):
    response = client.post("/api/v1/note/import", files={"file": ("test.txt", b"content", "text/plain")})
    assert response.status_code == 401


def test_import_note_unsupported_format(client, auth_token):
    response = client.post(
        "/api/v1/note/import",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("test.pdf", b"pdf content", "application/pdf")},
    )
    assert response.status_code == 400


def test_import_note_txt_success(client, auth_token):
    content = "这是一篇导入的笔记内容\n包含多行文本"
    response = client.post(
        "/api/v1/note/import",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("imported_note.txt", content.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "title" in data


def test_import_note_md_success(client, auth_token):
    content = "# 标题\n\n这是 Markdown 内容"
    response = client.post(
        "/api/v1/note/import",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("markdown_note.md", content.encode("utf-8"), "text/markdown")},
    )
    assert response.status_code == 200


# ============== 创建笔记补充分支 ==============

def test_create_note_duplicate_title(client, auth_token):
    _create_note(client, auth_token, "重复标题笔记")
    response = client.post(
        "/api/v1/note/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "重复标题笔记", "content": "<p>重复</p>"},
    )
    assert response.status_code == 409


def test_create_note_with_tags(client, auth_token):
    response = client.post(
        "/api/v1/note/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "带标签笔记", "content": "<p>内容</p>", "tags": "python,fastapi,测试"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tags"] == "python,fastapi,测试"


# ============== 更新笔记补充分支 ==============

def test_update_note_partial_fields(client, auth_token):
    note = _create_note(client, auth_token, "部分更新笔记")
    response = client.put(
        f"/api/v1/note/{note['id']}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "更新后的标题"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "更新后的标题"


# ============== 搜索补充分支 ==============

def test_search_with_pagination(client, auth_token):
    for i in range(3):
        _create_note(client, auth_token, f"分页搜索笔记{i}")
    response = client.get(
        "/api/v1/note/search?keyword=分页搜索&page=1&page_size=2",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
