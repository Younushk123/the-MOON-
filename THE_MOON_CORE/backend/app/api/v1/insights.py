from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_insight_service
from app.api.v1.responses import INVALID, NOT_FOUND
from app.models.envelope import Envelope, ok
from app.models.insight import AskRequest, Insight, InsightRequest
from app.services.module_services import InsightService

router = APIRouter(tags=["insights"])

Service = Annotated[InsightService, Depends(get_insight_service)]

PLACEHOLDER_NOTE = (
    "Until the module is connected, this returns `evidence_status: insufficient_evidence` with no claims."
)


@router.post(
    "/insights",
    response_model=Envelope[Insight],
    summary="Generate an evidence-backed insight",
    description=f"Every claim links to supporting evidence, or says evidence is insufficient. {PLACEHOLDER_NOTE}",
    responses={**NOT_FOUND, **INVALID},
)
def generate_insight(body: InsightRequest, service: Service) -> Envelope[Insight]:
    return ok(service.generate(body), data_mode=service.data_mode)


@router.post(
    "/assistant/ask",
    response_model=Envelope[Insight],
    summary="Ask a research question",
    description=f"Answered by the research assistant (RAG) over approved sources. {PLACEHOLDER_NOTE}",
    responses=INVALID,
)
def ask_assistant(body: AskRequest, service: Service) -> Envelope[Insight]:
    return ok(service.ask(body), data_mode=service.data_mode)
