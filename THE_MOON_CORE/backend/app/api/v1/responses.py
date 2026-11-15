"""OpenAPI documentation for error responses shared across routes."""

from app.models.envelope import ErrorEnvelope

INVALID = {422: {"model": ErrorEnvelope, "description": "Invalid parameters or request body (VALIDATION_ERROR)"}}
NOT_FOUND = {404: {"model": ErrorEnvelope, "description": "Experiment not found (EXPERIMENT_NOT_FOUND)"}}
