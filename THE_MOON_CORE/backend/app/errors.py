"""Error codes, application exceptions, and handlers that render every error in the envelope."""

import logging
from enum import Enum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models.envelope import ErrorDetail, ErrorEnvelope, Meta

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    EXPERIMENT_NOT_FOUND = "EXPERIMENT_NOT_FOUND"
    MEDIA_NOT_FOUND = "MEDIA_NOT_FOUND"
    MEDIA_EXPERIMENT_MISMATCH = "MEDIA_EXPERIMENT_MISMATCH"
    INCOMPATIBLE_MEASUREMENTS = "INCOMPATIBLE_MEASUREMENTS"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    HTTP_ERROR = "HTTP_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    """Raise from services or routes to return a structured error response."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class ExperimentNotFoundError(AppError):
    def __init__(self, experiment_ids: str | list[str]) -> None:
        ids = [experiment_ids] if isinstance(experiment_ids, str) else list(experiment_ids)
        if len(ids) == 1:
            message = f"The requested experiment '{ids[0]}' does not exist."
        else:
            message = f"The requested experiments do not exist: {', '.join(ids)}."
        super().__init__(
            ErrorCode.EXPERIMENT_NOT_FOUND, message, 404, details=[{"experiment_id": i} for i in ids]
        )


class MediaNotFoundError(AppError):
    def __init__(self, media_id: str) -> None:
        super().__init__(
            ErrorCode.MEDIA_NOT_FOUND,
            f"The requested media '{media_id}' does not exist.",
            404,
            details=[{"media_id": media_id}],
        )


class MediaExperimentMismatchError(AppError):
    def __init__(self, media_id: str, experiment_id: str, media_experiment_id: str) -> None:
        super().__init__(
            ErrorCode.MEDIA_EXPERIMENT_MISMATCH,
            f"Media '{media_id}' belongs to experiment '{media_experiment_id}', not '{experiment_id}'.",
            422,
            details=[{"media_id": media_id, "experiment_id": experiment_id, "media_experiment_id": media_experiment_id}],
        )


def _data_mode(request: Request) -> str | None:
    settings = getattr(request.app.state, "settings", None)
    return settings.data_mode if settings else None


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    body = ErrorEnvelope(
        error=ErrorDetail(code=code, message=message, details=details),
        meta=Meta(data_mode=_data_mode(request)),
    )
    return JSONResponse(status_code=status_code, content=jsonable_encoder(body))


_HTTP_CODES = {404: ErrorCode.NOT_FOUND, 405: ErrorCode.METHOD_NOT_ALLOWED}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return error_response(request, exc.status_code, exc.code.value, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"location": list(err.get("loc", [])), "message": err.get("msg"), "type": err.get("type")}
            for err in exc.errors()
        ]
        return error_response(
            request, 422, ErrorCode.VALIDATION_ERROR.value, "The request contains invalid parameters.", details
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _HTTP_CODES.get(exc.status_code, ErrorCode.HTTP_ERROR)
        return error_response(request, exc.status_code, code.value, str(exc.detail))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return error_response(request, 500, ErrorCode.INTERNAL_ERROR.value, "An unexpected error occurred.")
