"""Response envelope shared by every endpoint (PROJECT_CONTRACT.md section 5).

    {"success": bool, "data": ... | null, "error": {...} | null, "meta": {...}}
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from app.config import SCHEMA_VERSION, DataMode

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str = Field(description="Machine-readable error code, e.g. EXPERIMENT_NOT_FOUND.")
    message: str = Field(description="Human-readable explanation.")
    details: list[dict[str, Any]] | None = Field(
        default=None, description="Optional extra context, e.g. which fields failed validation."
    )


class Meta(BaseModel):
    schema_version: str = SCHEMA_VERSION
    data_mode: DataMode | None = None


class Envelope(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: ErrorDetail | None = None
    meta: Meta = Field(default_factory=Meta)


class Page(BaseModel, Generic[T]):
    items: list[T]
    count: int = Field(description="Total number of records matching the filters (across all pages).")
    page: int
    page_size: int


class ErrorEnvelope(Envelope[None]):
    """Documented shape of every error response."""

    success: bool = False
    error: ErrorDetail


def ok(data: T, data_mode: DataMode | None = None) -> Envelope[T]:
    return Envelope[T](success=True, data=data, meta=Meta(data_mode=data_mode))
