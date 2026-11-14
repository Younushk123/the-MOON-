"""Analysis and comparison requests/results (canonical schema v1.0, sections 4.4-4.5)."""

from typing import Literal

from pydantic import Field, field_validator

from app.models.base import Identifier, StrictModel, VariableName, ensure_unique

AnalysisType = Literal["statistical_summary"]
# PROVISIONAL: v1.0 only shows "success".
AnalysisStatus = Literal["success", "partial", "failed"]
ComparisonStatus = Literal["success", "partial", "not_comparable"]


# ---- Analysis ----

class AnalysisRequest(StrictModel):
    experiment_id: Identifier
    analysis_type: AnalysisType = "statistical_summary"
    variables: list[VariableName] | None = Field(
        default=None, min_length=1, max_length=20, description="Defaults to all of the experiment's measured variables."
    )

    _unique = field_validator("variables")(ensure_unique)


class AnalysisResultItem(StrictModel):
    metric: str
    variable: str
    value: int | float | None
    unit: str | None = None


class DataQuality(StrictModel):
    missing_values: int = Field(ge=0)
    validation_passed: bool
    warnings: list[str] = Field(default_factory=list)


class AnalysisResult(StrictModel):
    analysis_id: str
    experiment_id: str
    analysis_type: AnalysisType
    status: AnalysisStatus
    results: list[AnalysisResultItem] = Field(default_factory=list)
    data_quality: DataQuality
    source_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


# ---- Comparison ----

class ComparisonRequest(StrictModel):
    experiment_ids: list[Identifier] = Field(min_length=2, max_length=10)
    variables: list[VariableName] | None = Field(
        default=None, min_length=1, max_length=20, description="Defaults to every variable measured in any of the experiments."
    )

    _unique_ids = field_validator("experiment_ids")(ensure_unique)
    _unique_vars = field_validator("variables")(ensure_unique)


class ComparedVariable(StrictModel):
    variable: str
    unit: str | None = None
    comparable: bool
    reason: str | None = Field(default=None, description="Why the variable can't be compared. Null when comparable.")


class ExperimentValueSummary(StrictModel):
    experiment_id: str
    n: int
    mean: float
    min: float
    max: float


class ComparisonFinding(StrictModel):
    """PROVISIONAL: v1.0 leaves the shape of `findings` open."""

    variable: str
    unit: str | None = None
    values: list[ExperimentValueSummary]


class Comparison(StrictModel):
    comparison_id: str
    experiment_ids: list[str]
    status: ComparisonStatus
    compared_variables: list[ComparedVariable] = Field(default_factory=list)
    findings: list[ComparisonFinding] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
