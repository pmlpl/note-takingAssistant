"""app.api.v1.kg 知识图谱接口测试

通过 mock knowledge_graph_service 层来测试 API 接口，避免依赖真实图谱构建。
"""

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
    import os
    email = f"kg_test_{os.urandom(4).hex()}@example.com"
    password = "KgTest123456"
    client.post("/api/v1/user/register", json={"email": email, "password": password, "nickname": "kgtester"})
    response = client.post("/api/v1/user/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


# ============== GET /graph ==============

def test_get_kg_graph_requires_auth(client):
    response = client.get("/api/v1/kg/graph")
    assert response.status_code == 401


def test_get_kg_graph_with_cached_data(client, auth_token):
    mock_nodes = [{"id": "1", "label": "概念1", "type": "concept"}]
    mock_edges = [{"source": "1", "target": "2", "label": "相关", "type": "related"}]
    mock_stats = {"note_count": 5, "concept_count": 10, "relation_count": 8}

    with patch("app.api.v1.kg.get_kg_from_db", new_callable=AsyncMock) as mock_get_db:
        mock_get_db.return_value = (mock_nodes, mock_edges, mock_stats)
        response = client.get("/api/v1/kg/graph", headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert "stats" in data
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["label"] == "概念1"


def test_get_kg_graph_build_new(client, auth_token):
    mock_nodes = [{"id": "1", "label": "新概念", "type": "concept"}]
    mock_edges = [{"source": "1", "target": "2", "type": "related"}]
    mock_stats = {"note_count": 3, "concept_count": 5, "relation_count": 2}

    with patch("app.api.v1.kg.get_kg_from_db", new_callable=AsyncMock) as mock_get_db, \
         patch("app.api.v1.kg.build_knowledge_graph", new_callable=AsyncMock) as mock_build, \
         patch("app.api.v1.kg.save_kg_to_db", new_callable=AsyncMock) as mock_save, \
         patch("app.api.v1.kg.update_kg_status", new_callable=AsyncMock) as mock_status:
        mock_get_db.return_value = None
        mock_build.return_value = (mock_nodes, mock_edges, mock_stats)

        response = client.get("/api/v1/kg/graph", headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["label"] == "新概念"
    mock_save.assert_called_once()
    mock_status.assert_called_once()


def test_get_kg_graph_exception(client, auth_token):
    with patch("app.api.v1.kg.get_kg_from_db", new_callable=AsyncMock) as mock_get_db:
        mock_get_db.side_effect = Exception("Database error")
        response = client.get("/api/v1/kg/graph", headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 500
    assert "获取图谱失败" in response.json()["detail"]


# ============== POST /refresh ==============

def test_refresh_kg_requires_auth(client):
    response = client.post("/api/v1/kg/refresh")
    assert response.status_code == 401


def test_refresh_kg_success(client, auth_token):
    import asyncio as _real_asyncio
    with patch("app.api.v1.kg.get_kg_status", new_callable=AsyncMock) as mock_status, \
         patch("app.api.v1.kg.update_kg_status", new_callable=AsyncMock) as mock_update, \
         patch("app.api.v1.kg.build_knowledge_graph", new_callable=AsyncMock, return_value=([], [], {"note_count": 0})), \
         patch("app.api.v1.kg.save_kg_to_db", new_callable=AsyncMock), \
         patch("asyncio.create_task", wraps=_real_asyncio.create_task) as mock_create_task:
        mock_status.return_value = None  # 没有正在进行的任务
        response = client.post("/api/v1/kg/refresh", headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "generating"
    assert "图谱生成已开始" in data["message"]
    # update_kg_status 被主流程（generating）和背景任务（ready）各调用一次
    assert mock_update.call_count >= 1
    # create_task 至少被调用一次（含 _background_generate，wraps 会同时捕获 SQLAlchemy 内部调用）
    assert mock_create_task.call_count >= 1


def test_refresh_kg_already_generating(client, auth_token):
    mock_status = MagicMock()
    mock_status.status = "generating"

    with patch("app.api.v1.kg.get_kg_status", new_callable=AsyncMock) as mock_get_status:
        mock_get_status.return_value = mock_status
        response = client.post("/api/v1/kg/refresh", headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 409
    assert "图谱正在生成中" in response.json()["detail"]


def test_refresh_kg_with_ready_status(client, auth_token):
    import asyncio as _real_asyncio
    mock_status = MagicMock()
    mock_status.status = "ready"

    with patch("app.api.v1.kg.get_kg_status", new_callable=AsyncMock) as mock_get_status, \
         patch("app.api.v1.kg.update_kg_status", new_callable=AsyncMock), \
         patch("app.api.v1.kg.build_knowledge_graph", new_callable=AsyncMock, return_value=([], [], {"note_count": 0})), \
         patch("app.api.v1.kg.save_kg_to_db", new_callable=AsyncMock), \
         patch("asyncio.create_task", wraps=_real_asyncio.create_task):
        mock_get_status.return_value = mock_status
        response = client.post("/api/v1/kg/refresh", headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 200
    assert response.json()["status"] == "generating"


# ============== GET /status ==============

def test_get_kg_status_requires_auth(client):
    response = client.get("/api/v1/kg/status")
    assert response.status_code == 401


def test_get_kg_status_idle_when_no_status(client, auth_token):
    with patch("app.api.v1.kg.get_kg_status", new_callable=AsyncMock) as mock_get_status:
        mock_get_status.return_value = None
        response = client.get("/api/v1/kg/status", headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "idle"
    assert data["progress"] == 0
    assert data["total_notes"] == 0
    assert data["processed_notes"] == 0


def test_get_kg_status_generating(client, auth_token):
    mock_status = MagicMock()
    mock_status.status = "generating"
    mock_status.progress = 50
    mock_status.total_notes = 10
    mock_status.processed_notes = 5
    mock_status.error_msg = None
    mock_status.started_at = "2026-01-01T00:00:00"
    mock_status.finished_at = None

    with patch("app.api.v1.kg.get_kg_status", new_callable=AsyncMock) as mock_get_status:
        mock_get_status.return_value = mock_status
        response = client.get("/api/v1/kg/status", headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "generating"
    assert data["progress"] == 50
    assert data["total_notes"] == 10
    assert data["processed_notes"] == 5


def test_get_kg_status_ready(client, auth_token):
    mock_status = MagicMock()
    mock_status.status = "ready"
    mock_status.progress = 100
    mock_status.total_notes = 20
    mock_status.processed_notes = 20
    mock_status.error_msg = None
    mock_status.started_at = "2026-01-01T00:00:00"
    mock_status.finished_at = "2026-01-01T00:01:00"

    with patch("app.api.v1.kg.get_kg_status", new_callable=AsyncMock) as mock_get_status:
        mock_get_status.return_value = mock_status
        response = client.get("/api/v1/kg/status", headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["progress"] == 100


def test_get_kg_status_failed(client, auth_token):
    mock_status = MagicMock()
    mock_status.status = "failed"
    mock_status.progress = 30
    mock_status.total_notes = 10
    mock_status.processed_notes = 3
    mock_status.error_msg = "LLM connection error"
    mock_status.started_at = "2026-01-01T00:00:00"
    mock_status.finished_at = "2026-01-01T00:00:30"

    with patch("app.api.v1.kg.get_kg_status", new_callable=AsyncMock) as mock_get_status:
        mock_get_status.return_value = mock_status
        response = client.get("/api/v1/kg/status", headers={"Authorization": f"Bearer {auth_token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["error_msg"] == "LLM connection error"
