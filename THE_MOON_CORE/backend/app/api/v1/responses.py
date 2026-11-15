"""OpenAPI documentation for error responses shared across routes."""

from app.models.envelope import ErrorEnvelope

INVALID = {422: {"model": ErrorEnvelope, "description": "Invalid parameters or request body (VALIDATION_ERROR)"}}
NOT_FOUND = {404: {"model": ErrorEnvelope, "description": "Experiment not found (EXPERIMENT_NOT_FOUND)"}}
MEDIA_NOT_FOUND = {404: {"model": ErrorEnvelope, "description": "Media not found (MEDIA_NOT_FOUND)"}}
VISION_ERRORS = {
    404: {"model": ErrorEnvelope, "description": "Experiment or media not found (EXPERIMENT_NOT_FOUND, MEDIA_NOT_FOUND)"},
    422: {
        "model": ErrorEnvelope,
        "description": "Invalid request body (VALIDATION_ERROR), or the media belongs to another experiment "
        "(MEDIA_EXPERIMENT_MISMATCH)",
    },
}
