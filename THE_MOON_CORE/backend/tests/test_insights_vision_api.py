"""POST /insights, /assistant/ask, /vision/analyze. Placeholders must never invent results."""

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.adapters.mock_adapter import MockDataRepository
from app.config import Settings
from app.integrations import build_integrations
from app.main import create_app
from app.models.experiment import Experiment
from app.models.insight import Insight
from app.models.media import Media
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


class _RecordingAnalyzer:
    """Stands in for a CV module and records what the backend sends it."""

    def __init__(self) -> None:
        self.calls: list[tuple[Experiment, Media]] = []

    def analyze(self, experiment: Experiment, media: Media) -> CVResult:
        self.calls.append((experiment, media))
        return CVResult(
            cv_result_id="CV-TEST",
            experiment_id=experiment.experiment_id,
            media_id=media.media_id,
            processing_status="success",
            detected=True,
            method="test analyzer",
        )


class _RepoWithAvailableMedia(MockDataRepository):
    """The mock data, with MOCK-MEDIA-002 marked available and given a storage path."""

    def get_media(self, media_id: str) -> Media | None:
        media = super().get_media(media_id)
        if media is not None and media_id == "MOCK-MEDIA-002":
            media = media.model_copy(update={"availability_status": "available", "storage_path": "media/still.png"})
        return media


def _vision_client(analyzer: _RecordingAnalyzer, repository: MockDataRepository | None = None) -> TestClient:
    settings = Settings(data_mode="mock")
    integrations = replace(build_integrations(settings), vision=analyzer)
    return TestClient(create_app(settings, repository=repository, integrations=integrations))


def _assert_not_processed(data: dict) -> None:
    CVResult.model_validate(data)
    assert data["processing_status"] == "not_processed"
    assert data["detected"] is None
    assert all(v is None for v in data["features"].values())
    assert data["calibration_status"] == "not_calibrated"


def test_vision_unavailable_media_is_not_sent_to_module():
    analyzer = _RecordingAnalyzer()
    with _vision_client(analyzer) as client:
        body = {"experiment_id": "MOCK-EXP-001", "media_id": "MOCK-MEDIA-001"}
        data = assert_ok(client.post(f"{API}/vision/analyze", json=body))
    _assert_not_processed(data)
    assert data["media_id"] == "MOCK-MEDIA-001"
    assert data["source_ids"] == ["SRC-MOCK-001"]
    assert data["limitations"] == ["Media 'MOCK-MEDIA-001' is unavailable. No file was analysed."]
    assert analyzer.calls == []


def test_vision_available_media_is_sent_to_module():
    analyzer = _RecordingAnalyzer()
    with _vision_client(analyzer, _RepoWithAvailableMedia()) as client:
        body = {"experiment_id": "MOCK-EXP-001", "media_id": "MOCK-MEDIA-002"}
        data = assert_ok(client.post(f"{API}/vision/analyze", json=body))
    assert data["processing_status"] == "success"
    [(experiment, media)] = analyzer.calls
    assert experiment.experiment_id == "MOCK-EXP-001"
    assert media.media_id == "MOCK-MEDIA-002" and media.storage_path == "media/still.png"


def test_vision_placeholder_for_available_media():
    with TestClient(create_app(Settings(data_mode="mock"), repository=_RepoWithAvailableMedia())) as client:
        body = {"experiment_id": "MOCK-EXP-001", "media_id": "MOCK-MEDIA-002"}
        data = assert_ok(client.post(f"{API}/vision/analyze", json=body))
    _assert_not_processed(data)
    assert data["limitations"] == ["Computer vision module not connected. No media was analysed."]


def test_vision_unknown_experiment(client):
    body = {"experiment_id": "NOPE", "media_id": "MOCK-MEDIA-001"}
    assert_error(client.post(f"{API}/vision/analyze", json=body), 404, "EXPERIMENT_NOT_FOUND")


def test_vision_unknown_media(client):
    body = {"experiment_id": "MOCK-EXP-001", "media_id": "MEDIA-NOPE"}
    error = assert_error(client.post(f"{API}/vision/analyze", json=body), 404, "MEDIA_NOT_FOUND")
    assert error["details"] == [{"media_id": "MEDIA-NOPE"}]


def test_vision_media_from_another_experiment(client):
    body = {"experiment_id": "MOCK-EXP-002", "media_id": "MOCK-MEDIA-001"}
    error = assert_error(client.post(f"{API}/vision/analyze", json=body), 422, "MEDIA_EXPERIMENT_MISMATCH")
    assert error["details"] == [
        {"media_id": "MOCK-MEDIA-001", "experiment_id": "MOCK-EXP-002", "media_experiment_id": "MOCK-EXP-001"}
    ]


def test_vision_requires_media_id(client):
    assert_error(client.post(f"{API}/vision/analyze", json={"experiment_id": "MOCK-EXP-001"}), 422, "VALIDATION_ERROR")
