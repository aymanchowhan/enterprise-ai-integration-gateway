import os
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
HEADERS = {"X-Api-Key": os.environ.get("GATEWAY_API_KEY", "dev-secret-key")}

def test_approve_flags_low_rated_vendor():
    r = client.post("/approve", json={"po_id": "PO-1005"}, headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["decision"] == "Flagged for Review"

def test_approve_auto_approves_good_vendor():
    r = client.post("/approve", json={"po_id": "PO-1003"}, headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["decision"] == "Auto-Approved"

def test_approve_low_amount_skips_review():
    r = client.post("/approve", json={"po_id": "PO-1002"}, headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["decision"] == "Auto-Approved"

def test_approve_unknown_po_returns_404():
    r = client.post("/approve", json={"po_id": "PO-9999"}, headers=HEADERS)
    assert r.status_code == 404

def test_approve_requires_api_key():
    r = client.post("/approve", json={"po_id": "PO-1003"})
    assert r.status_code in (401, 422)