from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)


@pytest.fixture
def auth_token():
    email = f"test_{__name__}@example.com"
    password = "Test123456"

    client.post("/api/v1/user/register", json={
        "email": email,
        "password": password,
        "nickname": "testuser"
    })

    response = client.post("/api/v1/user/login", json={
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_register_success():
    email = f"register_test_{__name__}@example.com"
    password = "Register123"

    response = client.post("/api/v1/user/register", json={
        "email": email,
        "password": password,
        "nickname": "reguser"
    })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["email"] == email


def test_register_duplicate_email():
    email = f"dup_test_{__name__}@example.com"
    password = "Dup123456"

    client.post("/api/v1/user/register", json={
        "email": email,
        "password": password,
        "nickname": "dupuser"
    })

    response = client.post("/api/v1/user/register", json={
        "email": email,
        "password": password,
        "nickname": "dupuser2"
    })
    assert response.status_code == 400
    assert "该邮箱已被注册" in response.json()["detail"]


def test_register_invalid_password():
    response = client.post("/api/v1/user/register", json={
        "email": "invalid@example.com",
        "password": "short",
        "nickname": "invaliduser"
    })
    assert response.status_code == 400


def test_login_success():
    email = f"login_test_{__name__}@example.com"
    password = "Login123456"

    client.post("/api/v1/user/register", json={
        "email": email,
        "password": password,
        "nickname": "loginuser"
    })

    response = client.post("/api/v1/user/login", json={
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    email = f"wrongpwd_test_{__name__}@example.com"
    password = "Wrong123456"

    client.post("/api/v1/user/register", json={
        "email": email,
        "password": password,
        "nickname": "wrongpwduser"
    })

    response = client.post("/api/v1/user/login", json={
        "email": email,
        "password": "wrongpassword"
    })
    assert response.status_code == 401


def test_get_me_without_auth():
    response = client.get("/api/v1/user/me")
    assert response.status_code == 401


def test_get_me_with_auth(auth_token):
    response = client.get(
        "/api/v1/user/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data


def test_create_note_with_auth(auth_token):
    response = client.post(
        "/api/v1/note/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "title": "Test API Note",
            "content": "<p>This is a test note created via API</p>",
            "tags": "test,api",
            "is_favorite": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "Test API Note"


def test_get_note_list_with_auth(auth_token):
    response = client.get(
        "/api/v1/note/",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_note_detail_with_auth(auth_token):
    create_response = client.post(
        "/api/v1/note/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "title": "Detail Test Note",
            "content": "<p>Detail content</p>",
            "tags": "detail",
            "is_favorite": False
        }
    )
    note_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/note/{note_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == note_id
    assert data["title"] == "Detail Test Note"


def test_update_note_with_auth(auth_token):
    create_response = client.post(
        "/api/v1/note/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "title": "Update Test Note",
            "content": "<p>Original content</p>",
            "tags": "update",
            "is_favorite": False
        }
    )
    note_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/note/{note_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "title": "Updated Test Note",
            "content": "<p>Updated content</p>",
            "tags": "updated",
            "is_favorite": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == note_id
    assert data["title"] == "Updated Test Note"
    assert data["is_favorite"] == 1


def test_delete_note_with_auth(auth_token):
    create_response = client.post(
        "/api/v1/note/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "title": "Delete Test Note",
            "content": "<p>Will be deleted</p>",
            "tags": "delete",
            "is_favorite": False
        }
    )
    note_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/api/v1/note/{note_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert delete_response.status_code == 200

    get_response = client.get(
        f"/api/v1/note/{note_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert get_response.status_code == 404


def test_note_crud_without_auth():
    response = client.post("/api/v1/note/", json={
        "title": "Unauthorized Note",
        "content": "<p>Should fail</p>",
        "tags": "unauth",
        "is_favorite": False
    })
    assert response.status_code == 401

    response = client.get("/api/v1/note/")
    assert response.status_code == 401

    response = client.get("/api/v1/note/1")
    assert response.status_code == 401

    response = client.put("/api/v1/note/1", json={
        "title": "Update",
        "content": "<p>Update</p>"
    })
    assert response.status_code == 401

    response = client.delete("/api/v1/note/1")
    assert response.status_code == 401