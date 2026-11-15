from typing import Annotated

from fastapi import APIRouter, Path

from app.api.deps import Experiments
from app.api.v1.responses import INVALID, MEDIA_NOT_FOUND
from app.models.envelope import Envelope, ok
from app.models.media import Media

router = APIRouter(prefix="/media", tags=["media"])


@router.get(
    "/{media_id}",
    response_model=Envelope[Media],
    summary="Media record details",
    responses={**MEDIA_NOT_FOUND, **INVALID},
)
def get_media(service: Experiments, media_id: Annotated[str, Path(min_length=1, max_length=64)]) -> Envelope[Media]:
    return ok(service.get_media(media_id), data_mode=service.data_mode)
