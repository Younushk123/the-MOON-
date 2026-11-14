"""Experiment, Measurement and Source records (canonical schema v1.0, sections 4.1-4.3)."""

from datetime import date
from typing import Literal

from pydantic import Field

from app.models.base import Identifier, StrictModel, Url, VariableName

# PROVISIONAL: the v1.0 schema only shows "metadata_verified" as an example. The other
# values mirror Source.verification_status, plus "illustrative" for mock records.
ExperimentDataStatus = Literal["illustrative", "unverified", "metadata_verified", "content_verified"]
# PROVISIONAL: the v1.0 schema only shows "illustrative" as an example.
MeasurementStatus = Literal["illustrative", "unverified", "verified"]

SourceType = Literal["dataset", "research_paper", "technical_report", "webpage"]
AccessStatus = Literal["accessible", "restricted", "unavailable", "unknown"]
VerificationStatus = Literal["metadata_verified", "content_verified", "unverified"]
IngestionStatus = Literal["not_ingested", "ingested", "partially_ingested", "failed"]


class Experiment(StrictModel):
    experiment_id: Identifier
    name: str = Field(min_length=1)
    investigation: str | None = None
    program: str | None = None
    description: str | None = None
    platform: str | None = None
    source_ids: list[Identifier] = Field(default_factory=list)
    data_status: ExperimentDataStatus = "unverified"
    available_measurements: list[VariableName] = Field(
        default_factory=list, description="Variables that have at least one measurement record."
    )
    limitations: list[str] = Field(default_factory=list)
    last_updated: date | None = None


class MeasurementConditions(StrictModel):
    """Conditions a measurement was taken under. Unknown values are null, never zero.

    NOTE: v1.0 gives pressure/temperature/flow_velocity no units. Raised as an open question.
    """

    fuel: str | None = None
    pressure: float | None = None
    temperature: float | None = None
    flow_velocity: float | None = None


class Measurement(StrictModel):
    measurement_id: Identifier
    experiment_id: Identifier
    variable: VariableName
    value: float | None = None
    unit: str | None = None
    timestamp: str | None = Field(default=None, description="As recorded in the source (format not yet agreed).")
    conditions: MeasurementConditions = Field(default_factory=MeasurementConditions)
    source_id: Identifier | None = None
    measurement_status: MeasurementStatus = "unverified"
    notes: list[str] = Field(default_factory=list)


class Source(StrictModel):
    source_id: Identifier
    title: str = Field(min_length=1)
    url: Url | None = None
    publisher: str | None = None
    source_type: SourceType
    experiment_id: Identifier | None = None
    access_status: AccessStatus = "unknown"
    verification_status: VerificationStatus = "unverified"
    ingestion_status: IngestionStatus = "not_ingested"
    publication_date: str | None = Field(default=None, description="As given by the publisher, e.g. 2019 or 2019-05-02.")
