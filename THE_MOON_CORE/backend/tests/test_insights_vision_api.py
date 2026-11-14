"""POST /insights, /assistant/ask, /vision/analyze. Placeholders must never invent results."""

import pytest
from pydantic import ValidationError

from app.models.insight import Insight
from app.models.vision import CVResult
from tests.conftest import API, assert_error, assert_ok

QUESTION = "What can this experiment tell us about combustion in microgravity?"


def _assert_no_fabricated_insight(data: dict) -> None:
    Insight.model_validate(data)
    assert data["insight_id"].startswith("INSIGHT-")
    assert data["evidence_status"] == "insufficient_evidence"
    assert data["supporting_evidence"] == []
    assert data["confidence"] == "not_assessed"
    assert data["limitations"]


def test_insight_placeholder(client):
    body = {"question": QUESTION, "experiment_ids": ["MOCK-EXP-001"]}
    data = assert_ok(client.post(f"{API}/insights", json=body))
    _assert_no_fabricated_insight(data)
    assert data["question"] == QUESTION


def test_insight_without_experiments(client):
    _assert_no_fabricated_insight(assert_ok(client.post(f"{API}/insights", json={"question": QUESTION})))


def test_insight_unknown_experiment(client):
    body = {"question": QUESTION, "experiment_ids": ["NOPE"]}
    assert_error(client.post(f"{API}/insights", json=body), 404, "EXPERIMENT_NOT_FOUND")


def test_assistant_placeholder(client):
    data = assert_ok(client.post(f"{API}/assistant/ask", json={"question": "  Why are microgravity flames round?  "}))
    _assert_no_fabricated_insight(data)
    assert data["question"] == "Why are microgravity flames round?"


@pytest.mark.parametrize(
    "path, body",
    [
        ("/insights", {}),
        ("/insights", {"question": "hi"}),
        ("/insights", {"question": "x" * 1001}),
        ("/insights", {"question": QUESTION, "experiment_ids": ["A", "A"]}),
        ("/assistant/ask", {"question": "   "}),
        ("/assistant/ask", {"question": QUESTION, "experiment_ids": []}),
    ],
)
def test_invalid_insight_requests(client, path, body):
    assert_error(client.post(f"{API}{path}", json=body), 422, "VALIDATION_ERROR")


def test_supported_claim_without_evidence_is_rejected():
    with pytest.raises(ValidationError, match="supporting_evidence is required"):
        Insight(insight_id="I", question="q", claim="c", evidence_status="supported")


def test_vision_placeholder(client):
    body = {"experiment_id": "MOCK-EXP-001", "media_id": "MEDIA-001"}
    data = assert_ok(client.post(f"{API}/vision/analyze", json=body))
    CVResult.model_validate(data)
    assert data["processing_status"] == "not_processed"
    assert data["detected"] is None
    assert all(v is None for v in data["features"].values())
    assert data["calibration_status"] == "not_calibrated"


def test_vision_unknown_experiment(client):
    body = {"experiment_id": "NOPE", "media_id": "MEDIA-001"}
    assert_error(client.post(f"{API}/vision/analyze", json=body), 404, "EXPERIMENT_NOT_FOUND")


def test_vision_requires_media_id(client):
    assert_error(client.post(f"{API}/vision/analyze", json={"experiment_id": "MOCK-EXP-001"}), 422, "VALIDATION_ERROR")
