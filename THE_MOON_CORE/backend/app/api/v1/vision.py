from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_vision_service
from app.api.v1.responses import INVALID, NOT_FOUND
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
        "Pixel features are not physical flame dimensions unless `calibration_status` is `calibrated`. "
        "Until the module is connected, this returns `processing_status: not_processed`."
    ),
    responses={**NOT_FOUND, **INVALID},
)
def analyze_media(body: VisionRequest, service: Service) -> Envelope[CVResult]:
    return ok(service.analyze(body), data_mode=service.data_mode)
