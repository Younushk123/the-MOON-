"""Shared building blocks for all schema models."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class StrictModel(BaseModel):
    """Rejects unknown fields, so typos in requests and schema drift in adapters fail loudly."""

    model_config = ConfigDict(extra="forbid")


Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
VariableName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Url = Annotated[str, StringConstraints(pattern=r"^https?://\S+$", max_length=2048)]


def ensure_unique(values: list[str] | None) -> list[str] | None:
    if values is not None and len(set(values)) != len(values):
        raise ValueError("values must be unique")
    return values
