"""Computer vision integration for registered media and the supported FLEX video profile."""

import json
import logging
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from typing import Protocol

from PIL import Image, UnidentifiedImageError

from app.errors import AppError, ErrorCode
from app.ids import new_id
from app.models.experiment import Experiment
from app.models.vision import CVAnalysisJob, CVResult

logger = logging.getLogger(__name__)
FLEX_EXPERIMENT_ID = "PSI-69"
MAX_ACTIVE_VIDEO_JOBS = 2
MAX_STORED_VIDEO_JOBS = 20
MAX_IMAGE_PIXELS = 12_000_000
SUPPORTED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
IS_VERCEL = bool(os.getenv("VERCEL"))


class VisionAnalyzer(Protocol):
    def analyze(self, experiment: Experiment, media_id: str) -> CVResult: ...

    def analyze_uploaded_image(self, media_id: str, image_path: Path) -> CVResult: ...

    def submit_video(self, media_id: str, video_path: Path, upload_directory: Path) -> CVAnalysisJob: ...

    def get_video_job(self, job_id: str) -> CVAnalysisJob: ...


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

class FlexVisionAnalyzer(UnavailableVisionAnalyzer):
    def __init__(self) -> None:
        self._jobs: dict[str, CVAnalysisJob] = {}
        self._lock = Lock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="moon-flex-cv")

    def analyze_uploaded_image(self, media_id: str, image_path: Path) -> CVResult:
        try:
            with Image.open(image_path) as image:
                if image.format not in SUPPORTED_IMAGE_FORMATS:
                    raise AppError(
                        ErrorCode.VALIDATION_ERROR,
                        "Upload a JPEG, PNG, or WebP image.",
                        422,
                    )
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise AppError(
                        ErrorCode.PAYLOAD_TOO_LARGE,
                        "Image exceeds the 12 megapixel analysis limit.",
                        413,
                    )
                if getattr(image, "n_frames", 1) != 1:
                    raise AppError(
                        ErrorCode.VALIDATION_ERROR,
                        "Animated images are not supported; upload a single-frame image.",
                        422,
                    )
                image.verify()
        except AppError:
            raise
        except (Image.DecompressionBombError, UnidentifiedImageError, OSError, SyntaxError) as exc:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "The uploaded file is not a valid JPEG, PNG, or WebP image.",
                422,
            ) from exc

        repository_root = Path(__file__).resolve().parents[3]
        if str(repository_root) not in sys.path:
            sys.path.insert(0, str(repository_root))

        from computer_vision.src.backend_output import export_image_result
        from computer_vision.src.image_analysis import analyze_image

        try:
            _, decoded_image, red_signal, _ = analyze_image(image_path)
        except ValueError as exc:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "The uploaded file could not be decoded as an image.",
                422,
            ) from exc

        result = export_image_result(
            decoded_image,
            red_signal,
            experiment_id=FLEX_EXPERIMENT_ID,
            media_id=media_id,
        )
        result["cv_result_id"] = new_id("CV")
        return CVResult.model_validate(result)

    def submit_video(self, media_id: str, video_path: Path, upload_directory: Path) -> CVAnalysisJob:
        if IS_VERCEL:
            raise AppError(
                ErrorCode.ANALYSIS_FAILED,
                "Video analysis requires the persistent worker deployment. It is not available in the serverless API.",
                503,
            )

        with self._lock:
            active_jobs = sum(job.status in {"queued", "processing"} for job in self._jobs.values())
            if active_jobs >= MAX_ACTIVE_VIDEO_JOBS:
                raise AppError(
                    ErrorCode.ANALYSIS_BUSY,
                    "FLEX video analysis is busy. Please wait for an active upload to finish.",
                    429,
                )

            self._prune_jobs()
            job_id = new_id("CVJOB")
            job = CVAnalysisJob(job_id=job_id, status="queued")
            self._jobs[job_id] = job
            try:
                self._executor.submit(self._process_video, job_id, media_id, video_path, upload_directory)
            except RuntimeError as exc:
                del self._jobs[job_id]
                raise AppError(
                    ErrorCode.ANALYSIS_FAILED,
                    "FLEX video analysis is unavailable.",
                    503,
                ) from exc
            return job.model_copy(deep=True)

    def get_video_job(self, job_id: str) -> CVAnalysisJob:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise AppError(ErrorCode.NOT_FOUND, "FLEX video analysis job was not found.", 404)
            return job.model_copy(deep=True)

    def _prune_jobs(self) -> None:
        while len(self._jobs) >= MAX_STORED_VIDEO_JOBS:
            completed_id = next(
                (
                    job_id
                    for job_id, job in self._jobs.items()
                    if job.status in {"completed", "failed"}
                ),
                None,
            )
            if completed_id is None:
                return
            del self._jobs[completed_id]

    def _process_video(
        self,
        job_id: str,
        media_id: str,
        video_path: Path,
        upload_directory: Path,
    ) -> None:
        with self._lock:
            self._jobs[job_id] = CVAnalysisJob(job_id=job_id, status="processing")

        try:
            result = self._analyze_video(media_id, video_path)
            job = CVAnalysisJob(job_id=job_id, status="completed", result=result)
        except AppError as exc:
            job = CVAnalysisJob(job_id=job_id, status="failed", error=exc.message)
        except Exception:
            logger.exception("Unexpected error while analyzing FLEX video job %s", job_id)
            job = CVAnalysisJob(
                job_id=job_id,
                status="failed",
                error="FLEX video analysis failed. Please try again with the supported source video.",
            )
        finally:
            try:
                shutil.rmtree(upload_directory)
            except FileNotFoundError:
                pass
            except OSError:
                logger.exception("Could not remove temporary video upload directory %s", upload_directory)

        with self._lock:
            self._jobs[job_id] = job

    def _analyze_video(self, media_id: str, video_path: Path) -> CVResult:
        repository_root = Path(__file__).resolve().parents[3]
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "computer_vision.video_api",
                    "--video",
                    str(video_path),
                    "--media-id",
                    media_id,
                ],
                cwd=repository_root,
                capture_output=True,
                check=False,
                text=True,
                timeout=600,
            )
        except subprocess.TimeoutExpired as exc:
            raise AppError(
                ErrorCode.ANALYSIS_FAILED,
                "FLEX video analysis exceeded the 10-minute processing limit.",
            ) from exc

        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError:
            result = None

        if completed.returncode == 2 and isinstance(result, dict):
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                result.get("error", "The video does not match the supported FLEX profile."),
                422,
            )

        if completed.returncode != 0:
            logger.error(
                "FLEX video analyzer exited with code %s: %s",
                completed.returncode,
                completed.stderr[-2000:],
            )
            raise AppError(
                ErrorCode.ANALYSIS_FAILED,
                "FLEX video analysis failed.",
                500,
            )

        if not isinstance(result, dict):
            logger.error("FLEX video analyzer returned invalid JSON: %s", completed.stdout[:2000])
            raise AppError(
                ErrorCode.ANALYSIS_FAILED,
                "FLEX video analysis returned an invalid result.",
                500,
            )

        result["cv_result_id"] = new_id("CV")
        return CVResult.model_validate(result)
