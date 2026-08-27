from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200

def test_chat_rejects_missing_api_key():
    response = client.post("/chat", json={"message": "test"})
    assert response.status_code == 422  # missing required header

def test_chat_rejects_wrong_api_key():
    response = client.post(
        "/chat",
        json={"message": "test"},
        headers={"X-Api-Key": "wrong-key"}
    )
    assert response.status_code == 401