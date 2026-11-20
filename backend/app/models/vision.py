"""Computer vision requests and results (canonical schema v1.0, section 4.7, optional module)."""

from typing import Literal

from pydantic import Field

from app.models.base import Identifier, StrictModel

# PROVISIONAL: v1.0 only shows "success" and "not_calibrated".
ProcessingStatus = Literal["success", "failed", "not_processed"]
CalibrationStatus = Literal["not_calibrated", "calibrated"]


class CVFeatures(StrictModel):
    """Pixel-based features. Not physical flame dimensions unless calibration_status is 'calibrated'."""

    area_pixels: int | None = None
    width_pixels: int | None = None
    height_pixels: int | None = None
    brightness_mean: float | None = None


class CVResult(StrictModel):
    cv_result_id: str
    experiment_id: str
    media_id: str
    processing_status: ProcessingStatus
    detected: bool | None = None
    features: CVFeatures = Field(default_factory=CVFeatures)
    method: str | None = None
    calibration_status: CalibrationStatus = "not_calibrated"
    limitations: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


VideoJobStatus = Literal["queued", "processing", "completed", "failed"]


class CVAnalysisJob(StrictModel):
    job_id: Identifier
    status: VideoJobStatus
    result: CVResult | None = None
    error: str | None = None


class VisionRequest(StrictModel):
    experiment_id: Identifier
    media_id: Identifier
