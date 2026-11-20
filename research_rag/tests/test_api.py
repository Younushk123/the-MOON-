from fastapi.testclient import TestClient
from src.api import app, answer_question, get_rag

# Use fast extractive mode for unit tests without slow remote/heavy embedding calls
get_rag(mode="extractive", use_semantic=False)
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


def test_experiments_mapping():
    res = client.get("/experiments/mapping")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["count"] >= 10
    assert "integration_note" in data
    # Check EXP-001 mapping to BASS-II
    exp1 = next(e for e in data["experiments"] if e["canonical_id"] == "EXP-001")
    assert "BASS-II" in exp1["experiment_name"]
    assert exp1["psi_id"] == "PSI-25"
    assert "S28" in exp1["primary_sources"]
    assert "S29" in exp1["primary_sources"]


def test_ask_with_canonical_experiment_id():
    res = client.post("/ask", json={
        "query": "What fuel materials were tested?",
        "experiment_ids": ["EXP-001"]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]["resolved_experiments"]) > 0
    assert data["data"]["resolved_experiments"][0]["canonical_id"] == "EXP-001"
