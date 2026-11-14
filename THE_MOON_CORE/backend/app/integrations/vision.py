"""Computer vision integration point (optional module).

The placeholder reports that no media was processed. It never returns invented pixel features.
"""

from typing import Protocol

from app.ids import new_id
from app.models.experiment import Experiment
from app.models.vision import CVResult


class VisionAnalyzer(Protocol):
    def analyze(self, experiment: Experiment, media_id: str) -> CVResult: ...


class UnavailableVisionAnalyzer:
    def analyze(self, experiment: Experiment, media_id: str) -> CVResult:
        return CVResult(
            cv_result_id=new_id("CV"),
            experiment_id=experiment.experiment_id,
            media_id=media_id,
            processing_status="not_processed",
            detected=None,
            method=None,
            calibration_status="not_calibrated",
            limitations=["Computer vision module not connected. No media was analysed."],
            source_ids=[],
        )
