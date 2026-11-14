from fastapi.testclient import TestClient
from src.api import app, answer_question, get_rag

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "retrieval_mode" in data
    assert data["total_sources"] >= 34


def test_sources():
    res = client.get("/sources")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 34
    for src in data["sources"][:5]:
        assert "source_id" in src
        assert "title" in src
        assert src["source_url_verified"] == "unverified"
        assert src["specific_claims_verified"] == "unverified"
        assert src["raw_data_available"] == "unverified/no"


def test_ask_endpoint():
    res = client.post("/ask", json={"query": "What is the purpose of the NASA-STD-6001B flammability test procedures?"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "DOC-STD-6001B" in data["data"]["sources"]
    assert "claim" in data["data"]


def test_ask_empty():
    res = client.post("/ask", json={"query": "   "})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert data["error_code"] == "EMPTY_QUERY"


def test_answer_question_direct():
    out = answer_question("Why does the ISS fire alarm turn off ventilation?")
    assert "claim" in out
    assert "sources" in out
    assert "evidence" in out
    assert "conditions" in out
    assert "abstained" in out
