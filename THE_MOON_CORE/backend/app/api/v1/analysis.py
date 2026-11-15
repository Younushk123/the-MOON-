from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_analysis_service
from app.api.v1.responses import INVALID, NOT_FOUND
from app.models.analysis import AnalysisRequest, AnalysisResult, Comparison, ComparisonRequest
from app.models.envelope import Envelope, ok
from app.services.module_services import AnalysisService

router = APIRouter(tags=["analysis"])

Service = Annotated[AnalysisService, Depends(get_analysis_service)]


@router.post(
    "/analysis",
    response_model=Envelope[AnalysisResult],
    summary="Run a supported analysis",
    description=(
        "Supported `analysis_type`: `statistical_summary` (count, mean, min, max per variable). "
        "`status` is `partial` or `failed` when some or all variables couldn't be summarised; "
        "see `data_quality.warnings` for why."
    ),
    responses={**NOT_FOUND, **INVALID},
)
def run_analysis(body: AnalysisRequest, service: Service) -> Envelope[AnalysisResult]:
    return ok(service.analyze(body), data_mode=service.data_mode)


@router.post(
    "/comparison",
    response_model=Envelope[Comparison],
    summary="Compare experiments",
    description=(
        "A variable is compared only when every experiment has values for it, units match, and recorded "
        "measurement conditions don't conflict. Otherwise it is listed with `comparable: false` and a `reason`."
    ),
    responses={**NOT_FOUND, **INVALID},
)
def compare_experiments(body: ComparisonRequest, service: Service) -> Envelope[Comparison]:
    return ok(service.compare(body), data_mode=service.data_mode)
