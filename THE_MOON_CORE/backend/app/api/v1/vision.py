from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_vision_service
from app.api.v1.responses import VISION_ERRORS
from app.models.envelope import Envelope, ok
from app.models.vision import CVResult, VisionRequest
from app.services.module_services import VisionService

router = APIRouter(tags=["vision"])

Service = Annotated[VisionService, Depends(get_vision_service)]


@router.post(
    "/vision/analyze",
    response_model=Envelope[CVResult],
    summary="Analyze flame media (optional module)",
    description=(
        "The media must belong to the experiment. Media that isn't `available` is not sent to the CV module "
        "and returns `processing_status: not_processed`. "
        "Pixel features are not physical flame dimensions unless `calibration_status` is `calibrated`. "
        "Until the module is connected, every request returns `processing_status: not_processed`."
    ),
    responses=VISION_ERRORS,
)
def analyze_media(body: VisionRequest, service: Service) -> Envelope[CVResult]:
    return ok(service.analyze(body), data_mode=service.data_mode)
