import logging
import shutil
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_vision_service
from app.errors import AppError, ErrorCode
from app.api.v1.responses import INVALID, NOT_FOUND
from app.models.envelope import Envelope, ok
from app.models.base import Identifier
from app.models.vision import CVAnalysisJob, CVResult, VisionRequest
from app.services.module_services import VisionService

router = APIRouter(tags=["vision"])

Service = Annotated[VisionService, Depends(get_vision_service)]
MAX_VIDEO_SIZE = 4 * 1024 * 1024
MAX_IMAGE_SIZE = 25 * 1024 * 1024
SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
logger = logging.getLogger(__name__)


@router.post(
    "/vision/analyze",
    response_model=Envelope[CVResult],
    summary="Analyze flame media (optional module)",
    description=(
        "Pixel features are not physical flame dimensions unless `calibration_status` is `calibrated`. "
        "An ID-only request has no file to process and returns `processing_status: not_processed`; "
        "use `/vision/analyze-video` for the supported PSI-69 FLEX MP4."
    ),
    responses={**NOT_FOUND, **INVALID},
)
def analyze_media(body: VisionRequest, service: Service) -> Envelope[CVResult]:
    return ok(service.analyze(body), data_mode=service.data_mode)


@router.post(
    "/vision/analyze-image",
    response_model=Envelope[CVResult],
    summary="Analyze an uploaded PSI-69 FLEX still image",
    description=(
        "Accepts a single-frame JPEG, PNG, or WebP image up to 25 MB and 12 megapixels. "
        "The result reports red-excess luminous-region features, not a confirmed flame. "
        "Uploads are temporary and are not retained."
    ),
    responses={**INVALID, 413: {"description": "Image exceeds the upload or pixel limit"}},
)
async def analyze_flex_image(
    media_id: Annotated[Identifier, Form()],
    image: Annotated[UploadFile, File()],
    service: Service,
) -> Envelope[CVResult]:
    suffix = Path(image.filename or "").suffix.lower()
    if suffix not in SUPPORTED_IMAGE_SUFFIXES:
        await image.close()
        raise AppError(ErrorCode.VALIDATION_ERROR, "Upload a JPEG, PNG, or WebP image.", 422)

    upload_directory = Path(tempfile.mkdtemp(prefix="moon-image-upload-"))
    try:
        image_path = upload_directory / f"upload{suffix}"
        size = 0
        with image_path.open("wb") as destination:
            while chunk := await image.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_IMAGE_SIZE:
                    raise AppError(
                        ErrorCode.PAYLOAD_TOO_LARGE,
                        "Image exceeds the 25 MB upload limit.",
                        413,
                    )
                destination.write(chunk)

        if size == 0:
            raise AppError(ErrorCode.VALIDATION_ERROR, "The uploaded image is empty.", 422)

        result = await run_in_threadpool(service.analyze_uploaded_image, media_id, image_path)
        return ok(result, data_mode=service.data_mode)
    finally:
        await image.close()
        try:
            shutil.rmtree(upload_directory)
        except FileNotFoundError:
            pass
        except OSError:
            logger.exception("Could not remove temporary image upload directory %s", upload_directory)


@router.post(
    "/vision/analyze-video",
    response_model=Envelope[CVAnalysisJob],
    status_code=202,
    summary="Queue the supported FLEX video for analysis",
    description=(
        "Accepts an MP4 matching the PSI-69 FLEX profile (960x540, 30 FPS, 693 frames). "
        "Returns a job ID immediately; poll `/vision/jobs/{job_id}` for status. "
        "Uploads are temporary, limited to 4 MB for serverless deployment, and are not retained."
    ),
    responses={**INVALID, 413: {"description": "Video exceeds the 4 MB serverless upload limit"}},
)
async def analyze_flex_video(
    media_id: Annotated[Identifier, Form()],
    video: Annotated[UploadFile, File()],
    service: Service,
) -> Envelope[CVAnalysisJob]:
    if not video.filename or Path(video.filename).suffix.lower() != ".mp4":
        await video.close()
        raise AppError(ErrorCode.VALIDATION_ERROR, "Upload an MP4 video file.", 422)

    upload_directory = Path(tempfile.mkdtemp(prefix="moon-video-upload-"))
    transferred_to_worker = False
    try:
        video_path = upload_directory / "upload.mp4"
        size = 0
        with video_path.open("wb") as destination:
            while chunk := await video.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_VIDEO_SIZE:
                    raise AppError(
                        ErrorCode.PAYLOAD_TOO_LARGE,
                        "Video exceeds the 25 MB upload limit.",
                        413,
                    )
                destination.write(chunk)

        if size == 0:
            raise AppError(ErrorCode.VALIDATION_ERROR, "The uploaded video is empty.", 422)

        job = await run_in_threadpool(
            service.submit_video,
            media_id,
            video_path,
            upload_directory,
        )
        transferred_to_worker = True
        return ok(job, data_mode=service.data_mode)
    finally:
        await video.close()
        if not transferred_to_worker:
            try:
                shutil.rmtree(upload_directory)
            except FileNotFoundError:
                pass
            except OSError:
                logger.exception("Could not remove temporary video upload directory %s", upload_directory)


@router.get(
    "/vision/jobs/{job_id}",
    response_model=Envelope[CVAnalysisJob],
    summary="Get FLEX video analysis job status",
    responses={**NOT_FOUND},
)
def get_flex_video_job(job_id: Identifier, service: Service) -> Envelope[CVAnalysisJob]:
    return ok(service.get_video_job(job_id), data_mode=service.data_mode)
