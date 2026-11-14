from fastapi import FastAPI
from fastapi.testclient import TestClient
from rag_pipeline import NASARAG
from src.api_adapter import ask_research, build_router

RAG = NASARAG(mode="extractive", use_semantic=False)


def test_ask_research_shape_and_abstention():
    out = ask_research(RAG, "What exact oxygen threshold did BASS-II measure?", ["PSI-25"])
    assert out["abstained"] and out["evidence_status"] == "insufficient_evidence"
    for k in ("claim", "supporting_evidence", "nasa_source", "experiment_conditions", "fire_safety_relevance",
              "limitations", "data_status", "validated_findings", "retrieved"):
        assert k in out
    assert out["team_status_label"] == "Insufficient evidence"


def test_unknown_experiment_id_warns_not_crashes():
    out = ask_research(RAG, "Why do flames turn spherical in microgravity?", ["PSI-9999"])
    assert any("PSI-9999" in w for w in out["warnings"])


def test_validated_findings_passed_through_separately():
    vf = [{"analysis_id": "ANALYSIS-001", "note": "from data module"}]
    out = ask_research(RAG, "Why do flames turn spherical in microgravity?", validated_findings=vf)
    assert out["validated_findings"] == vf and all(e["content_type"] != "validated" for e in out["supporting_evidence"])


def test_endpoint_envelope():
    app = FastAPI(); app.include_router(build_router(RAG)); c = TestClient(app)
    r = c.post("/api/v1/assistant/ask", json={"question": "  "}).json()
    assert r["success"] is False and r["error_code"] == "EMPTY_QUESTION"
    r = c.post("/api/v1/assistant/ask", json={"question": "Why does the ISS fire alarm turn off ventilation?"}).json()
    assert r["success"] is True and "claim" in r["data"]
