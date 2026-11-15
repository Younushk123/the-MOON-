"""AI / RAG insight requests and results (canonical schema v1.0, section 4.6)."""

from typing import Annotated, Literal

from pydantic import Field, StringConstraints, field_validator, model_validator

from app.models.base import Identifier, StrictModel, Url, ensure_unique

EvidenceStatus = Literal["supported", "partially_supported", "insufficient_evidence"]
# Qualitative only: v1.0 forbids a numerical score without a validated scoring method.
# PROVISIONAL: v1.0 only shows "not_assessed".
Confidence = Literal["not_assessed", "low", "medium", "high"]

Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=1000)]


class Evidence(StrictModel):
    source_id: Identifier
    experiment_id: Identifier | None = None
    evidence_text: str = Field(min_length=1)
    url: Url | None = None


class Insight(StrictModel):
    insight_id: str
    question: str
    claim: str
    supporting_evidence: list[Evidence] = Field(default_factory=list)
    fire_safety_relevance: str | None = None
    limitations: list[str] = Field(default_factory=list)
    confidence: Confidence = "not_assessed"
    evidence_status: EvidenceStatus

    @model_validator(mode="after")
    def _claims_need_evidence(self) -> "Insight":
        if self.evidence_status != "insufficient_evidence" and not self.supporting_evidence:
            raise ValueError("supporting_evidence is required unless evidence_status is 'insufficient_evidence'")
        return self


class InsightRequest(StrictModel):
    question: Question
    experiment_ids: list[Identifier] = Field(default_factory=list, max_length=10)

    _unique = field_validator("experiment_ids")(ensure_unique)


class AskRequest(StrictModel):
    question: Question
