"""Computer vision integration point (optional module).

The backend only calls analyze() for media that belongs to the experiment and is available,
so a module always receives a Media record that says where the file is (file_url or storage_path).

The placeholder reports that no media was processed. It never returns invented pixel features.
"""

from typing import Protocol

from app.ids import new_id
from app.models.experiment import Experiment
from app.models.media import Media
from app.models.vision import CVResult


class VisionAnalyzer(Protocol):
    def analyze(self, experiment: Experiment, media: Media) -> CVResult: ...


def not_processed(experiment: Experiment, media: Media, reason: str) -> CVResult:
    """A CVResult stating that nothing was analysed, and why."""
    return CVResult(
        cv_result_id=new_id("CV"),
        experiment_id=experiment.experiment_id,
        media_id=media.media_id,
        processing_status="not_processed",
        detected=None,
        method=None,
        calibration_status="not_calibrated",
        limitations=[reason],
        source_ids=[media.source_id] if media.source_id else [],
    )


class UnavailableVisionAnalyzer:
    def analyze(self, experiment: Experiment, media: Media) -> CVResult:
        return not_processed(experiment, media, "Computer vision module not connected. No media was analysed.")
