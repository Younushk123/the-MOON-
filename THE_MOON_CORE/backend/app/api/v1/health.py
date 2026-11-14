from fastapi import APIRouter, Request

from app.models.envelope import Envelope, ok

router = APIRouter(tags=["health"])


@router.get("/health", response_model=Envelope[dict[str, str]], summary="Service health check")
def health(request: Request) -> Envelope[dict[str, str]]:
    return ok({"status": "ok"}, data_mode=request.app.state.settings.data_mode)
