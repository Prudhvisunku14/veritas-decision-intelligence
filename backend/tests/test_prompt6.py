import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_fastapi_health_routes():
    res1 = client.get("/health")
    res2 = client.get("/api/health")

    assert res1.status_code == 200
    assert res1.json()["status"] == "ok"

    assert res2.status_code == 200
    assert res2.json()["status"] == "ok"


def test_fastapi_kpis_routes():
    res = client.get("/api/kpis")
    assert res.status_code == 200
    data = res.json()
    assert "revenue" in data
    assert "orders" in data
    assert "conversion_rate" in data
    assert "aov" in data
    assert "gross_margin" in data


def test_fastapi_insight_route():
    headers = {"X-Demo-User": "ceo"}
    res = client.get("/api/insight", params={"kpi": "revenue", "region": "North", "scenario": "main"}, headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert "evidence" in data
    assert "narrative" in data
    assert "actions" in data
    assert "telemetry" in data["evidence"]
    assert data["evidence"]["region"] == "North"
    assert data["evidence"]["kpi"] == "revenue"


def test_fastapi_security_scoping():
    headers = {"X-Demo-User": "north_mgr"}
    res = client.get("/api/insight", params={"kpi": "revenue", "region": "South", "scenario": "main"}, headers=headers)

    assert res.status_code == 403
    assert "North" in res.json()["detail"]


def test_fastapi_ask_route():
    headers = {"X-Demo-User": "ceo"}

    # Test "why did revenue decline?"
    res1 = client.post("/api/ask", json={"question": "Why did revenue decline?", "region": "North", "kpi": "revenue"}, headers=headers)
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["intent"] == "explain_decline"
    assert "Revenue" in d1["answer"]

    # Test "what should I do?"
    res2 = client.post("/api/ask", json={"question": "What should I do?", "region": "North", "kpi": "revenue"}, headers=headers)
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["intent"] == "recommend_actions"

    # Test "why are you uncertain about marketing?"
    res3 = client.post("/api/ask", json={"question": "Why are you uncertain about marketing?", "region": "North", "kpi": "revenue", "scenario": "degraded"}, headers=headers)
    assert res3.status_code == 200
    d3 = res3.json()
    assert d3["intent"] == "explain_uncertainty"

    # Test "show the evidence."
    res4 = client.post("/api/ask", json={"question": "Show the evidence.", "region": "North", "kpi": "revenue"}, headers=headers)
    assert res4.status_code == 200
    d4 = res4.json()
    assert d4["intent"] == "show_evidence"
    assert "Query ID" in d4["answer"]


def test_fastapi_feedback_route():
    headers = {"X-Demo-User": "ceo"}
    payload = {
        "insight_id": "ins_test_456",
        "user_id": "ceo",
        "rating": "up",
        "comment": "Accurate bridge decomposition.",
    }
    res = client.post("/api/feedback", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "stored"


def test_fastapi_telemetry_route():
    headers = {"X-Demo-User": "ceo"}
    res = client.get("/api/telemetry", headers=headers)
    assert res.status_code == 200
    assert "data" in res.json()


def test_fastapi_sparse_history_route():
    headers = {"X-Demo-User": "ceo"}
    res = client.get("/api/sparse-history/P020", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["product_id"] == "P020"
    assert data["evidence_confidence_cap"] <= 0.60
    assert "Insufficient history — cohort benchmark used." in data["message"]


def test_evidence_by_id_route():
    headers = {"X-Demo-User": "ceo"}
    res = client.get("/api/evidence/ins_test_789", headers=headers)
    assert res.status_code == 200
    assert res.json()["insight_id"] == "ins_test_789"
