"""POST /insights, /assistant/ask, /vision/analyze. Placeholders must never invent results."""

import pytest
from pydantic import ValidationError

from app.integrations.rag_adapter import NASAResearchAssistant
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


def test_assistant_without_evidence(client, monkeypatch):
    def fake_ask(self, question, experiment_ids=None, validated_findings=None, top_k=5):
        return Insight(
            insight_id="INSIGHT-TEST",
            question=question,
            claim="No evidence-backed answer is available.",
            limitations=["No analysis was performed."],
            evidence_status="insufficient_evidence",
        )

    monkeypatch.setattr(NASAResearchAssistant, "ask", fake_ask)

    data = assert_ok(client.post(f"{API}/assistant/ask", json={"question": "  Why are microgravity flames round?  "}))
    _assert_no_fabricated_insight(data)
    assert data["question"] == "Why are microgravity flames round?"


def test_assistant_forwards_experiment_scope(client, monkeypatch):
    received = {}

    def fake_ask(self, question, experiment_ids=None, validated_findings=None, top_k=5):
        received.update(
            question=question,
            experiment_ids=experiment_ids,
            validated_findings=validated_findings,
            top_k=top_k,
        )
        return Insight(
            insight_id="INSIGHT-TEST",
            question=question,
            claim="Insufficient evidence.",
            evidence_status="insufficient_evidence",
        )

    monkeypatch.setattr(NASAResearchAssistant, "ask", fake_ask)

    data = assert_ok(
        client.post(
            f"{API}/assistant/ask",
            json={
                "question": QUESTION,
                "experiment_ids": ["PSI159-CFIG-NORMAL"],
                "top_k": 3,
            },
        )
    )

    assert data["question"] == QUESTION
    assert received == {
        "question": QUESTION,
        "experiment_ids": ["PSI159-CFIG-NORMAL"],
        "validated_findings": None,
        "top_k": 3,
    }


@pytest.mark.parametrize(
    "path, body",
    [
        ("/insights", {}),
        ("/insights", {"question": "hi"}),
        ("/insights", {"question": "x" * 1001}),
        ("/insights", {"question": QUESTION, "experiment_ids": ["A", "A"]}),
        ("/assistant/ask", {"question": "   "}),
        ("/assistant/ask", {"question": QUESTION, "top_k": 0}),
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


def test_flex_image_upload_returns_result_and_cleans_upload(client, monkeypatch):
    from app.integrations.vision import FlexVisionAnalyzer

    received = {}
    result = CVResult(
        cv_result_id="CV-TEST",
        experiment_id="PSI-69",
        media_id="MEDIA-002",
        processing_status="success",
        detected=True,
        features={"area_pixels": 600, "width_pixels": 30, "height_pixels": 20, "brightness_mean": 200},
        method="red_excess_connected_component_segmentation",
        calibration_status="not_calibrated",
    )

    def fake_analyze_uploaded_image(self, media_id, image_path):
        received["media_id"] = media_id
        received["image"] = image_path.read_bytes()
        received["upload_directory"] = image_path.parent
        return result

    monkeypatch.setattr(FlexVisionAnalyzer, "analyze_uploaded_image", fake_analyze_uploaded_image)
    data = assert_ok(
        client.post(
            f"{API}/vision/analyze-image",
            data={"media_id": "MEDIA-002"},
            files={"image": ("flame.png", b"image-bytes", "image/png")},
        )
    )

    CVResult.model_validate(data)
    assert data == result.model_dump()
    assert received["media_id"] == "MEDIA-002"
    assert received["image"] == b"image-bytes"
    assert not received["upload_directory"].exists()


def test_flex_image_upload_rejects_invalid_image(client):
    response = client.post(
        f"{API}/vision/analyze-image",
        data={"media_id": "MEDIA-002"},
        files={"image": ("flame.png", b"not-an-image", "image/png")},
    )
    assert_error(response, 422, "VALIDATION_ERROR")


def test_flex_image_upload_rejects_unsupported_format(client):
    response = client.post(
        f"{API}/vision/analyze-image",
        data={"media_id": "MEDIA-002"},
        files={"image": ("flame.gif", b"image-bytes", "image/gif")},
    )
    assert_error(response, 422, "VALIDATION_ERROR")


def test_flex_image_upload_enforces_size_limit(client, monkeypatch):
    from app.api.v1 import vision as vision_api

    monkeypatch.setattr(vision_api, "MAX_IMAGE_SIZE", 4)
    response = client.post(
        f"{API}/vision/analyze-image",
        data={"media_id": "MEDIA-002"},
        files={"image": ("flame.png", b"12345", "image/png")},
    )
    assert_error(response, 413, "PAYLOAD_TOO_LARGE")


def test_flex_image_analyzer_returns_psi69_result(tmp_path):
    import cv2
    import numpy as np

    from app.integrations.vision import FlexVisionAnalyzer

    image_path = tmp_path / "flame.png"
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[20:40, 20:50, 2] = 200
    assert cv2.imwrite(str(image_path), image)

    result = FlexVisionAnalyzer().analyze_uploaded_image("MEDIA-002", image_path)

    assert result.cv_result_id.startswith("CV-")
    assert result.experiment_id == "PSI-69"
    assert result.media_id == "MEDIA-002"
    assert result.detected is True
    assert result.features.area_pixels == 600
    assert result.method == "red_excess_connected_component_segmentation"


def test_flex_image_analyzer_rejects_images_over_pixel_limit(tmp_path):
    from PIL import Image

    from app.errors import AppError
    from app.integrations.vision import FlexVisionAnalyzer

    image_path = tmp_path / "large.png"
    Image.new("RGB", (3500, 3500), "black").save(image_path)

    with pytest.raises(AppError) as error:
        FlexVisionAnalyzer().analyze_uploaded_image("MEDIA-002", image_path)

    assert error.value.status_code == 413


def test_flex_video_upload_returns_job(client, monkeypatch):
    import shutil

    from app.integrations.vision import FlexVisionAnalyzer
    from app.models.vision import CVAnalysisJob

    received = {}

    def fake_submit_video(self, media_id, video_path, upload_directory):
        received["media_id"] = media_id
        received["video"] = video_path.read_bytes()
        shutil.rmtree(upload_directory)
        return CVAnalysisJob(job_id="CVJOB-TEST", status="queued")

    monkeypatch.setattr(FlexVisionAnalyzer, "submit_video", fake_submit_video)

    response = client.post(
        f"{API}/vision/analyze-video",
        data={"media_id": "MEDIA-001"},
        files={"video": ("flex.mp4", b"video-bytes", "video/mp4")},
    )
    data = assert_ok(response, status=202)

    CVAnalysisJob.model_validate(data)
    assert data == {
        "job_id": "CVJOB-TEST",
        "status": "queued",
        "result": None,
        "error": None,
    }
    assert received == {"media_id": "MEDIA-001", "video": b"video-bytes"}


def test_flex_video_job_runs_in_background_and_cleans_upload(tmp_path, monkeypatch):
    import time

    from app.integrations.vision import FlexVisionAnalyzer
    from app.models.vision import CVAnalysisJob

    analyzer = FlexVisionAnalyzer()
    upload_directory = tmp_path / "upload"
    upload_directory.mkdir()
    video_path = upload_directory / "upload.mp4"
    video_path.write_bytes(b"video")
    expected = CVResult(
        cv_result_id="CV-TEST",
        experiment_id="PSI-69",
        media_id="MEDIA-001",
        processing_status="success",
        detected=True,
        features={"area_pixels": 100, "width_pixels": 10, "height_pixels": 10, "brightness_mean": 50},
        method="phase_gated_ransac_circle",
        calibration_status="not_calibrated",
    )
    monkeypatch.setattr(analyzer, "_analyze_video", lambda media_id, path: expected)

    queued = analyzer.submit_video("MEDIA-001", video_path, upload_directory)
    assert queued.status == "queued"

    for _ in range(100):
        job = analyzer.get_video_job(queued.job_id)
        if job.status in {"completed", "failed"}:
            break
        time.sleep(0.01)

    CVAnalysisJob.model_validate(job)
    assert job.status == "completed"
    assert job.result == expected
    assert not upload_directory.exists()


def test_flex_video_job_status_returns_completed_result(client, monkeypatch):
    from app.integrations.vision import FlexVisionAnalyzer
    from app.models.vision import CVAnalysisJob

    result = CVResult(
        cv_result_id="CV-TEST",
        experiment_id="PSI-69",
        media_id="MEDIA-001",
        processing_status="success",
        detected=True,
        features={"area_pixels": 100, "width_pixels": 10, "height_pixels": 10, "brightness_mean": 50},
        method="phase_gated_ransac_circle",
        calibration_status="not_calibrated",
    )
    monkeypatch.setattr(
        FlexVisionAnalyzer,
        "get_video_job",
        lambda self, job_id: CVAnalysisJob(job_id=job_id, status="completed", result=result),
    )

    data = assert_ok(client.get(f"{API}/vision/jobs/CVJOB-TEST"))
    assert data["status"] == "completed"
    assert data["result"]["experiment_id"] == "PSI-69"
    assert data["result"]["features"]["area_pixels"] == 100


def test_flex_video_upload_rejects_non_mp4(client):
    response = client.post(
        f"{API}/vision/analyze-video",
        data={"media_id": "MEDIA-001"},
        files={"video": ("flex.mov", b"video-bytes", "video/quicktime")},
    )
    assert_error(response, 422, "VALIDATION_ERROR")


def test_flex_video_upload_enforces_size_limit(client, monkeypatch):
    from app.api.v1 import vision as vision_api

    monkeypatch.setattr(vision_api, "MAX_VIDEO_SIZE", 4)
    response = client.post(
        f"{API}/vision/analyze-video",
        data={"media_id": "MEDIA-001"},
        files={"video": ("flex.mp4", b"12345", "video/mp4")},
    )
    assert_error(response, 413, "PAYLOAD_TOO_LARGE")
