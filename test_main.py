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
def test_odata_returns_all_orders():
    response = client.get("/odata/PurchaseOrders")
    assert response.status_code == 200
    assert len(response.json()["value"]) >= 5

def test_odata_filter():
    response = client.get("/odata/PurchaseOrders?$filter=status eq 'Approved'")
    assert response.status_code == 200
    results = response.json()["value"]
    assert all(r["status"] == "Approved" for r in results)

def test_odata_expand():
    response = client.get("/odata/PurchaseOrders?$expand=Vendor&$top=1")
    results = response.json()["value"]
    assert "Vendor" in results[0]
    assert "name" in results[0]["Vendor"]