from fastapi.testclient import TestClient

from main import app


def test_root_returns_json_message():
    with TestClient(app) as client:
        r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
    assert "运行成功" in data["message"] or "成功" in data["message"]
