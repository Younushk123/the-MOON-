"""AI insight and RAG assistant protocols with explicit unavailable fallbacks.

The RAG adapter is connected separately; unavailable implementations never generate
claims or cite evidence.
"""

from typing import Any, Protocol

from app.ids import new_id
from app.models.experiment import Experiment
from app.models.insight import Insight


class InsightEngine(Protocol):
    def generate(self, question: str, experiments: list[Experiment]) -> Insight: ...


class ResearchAssistant(Protocol):
    def ask(
        self,
        question: str,
        experiment_ids: list[str] | None = None,
        validated_findings: list[dict[str, Any]] | None = None,
        top_k: int = 5,
    ) -> Insight: ...


def _unavailable(question: str, module: str) -> Insight:
    return Insight(
        insight_id=new_id("INSIGHT"),
        question=question,
        claim=f"No evidence-backed answer is available: the {module} module is not connected yet.",
        supporting_evidence=[],
        fire_safety_relevance=None,
        limitations=[f"{module[0].upper()}{module[1:]} module not connected. No analysis was performed."],
        confidence="not_assessed",
        evidence_status="insufficient_evidence",
    )


class UnavailableInsightEngine:
    def generate(self, question: str, experiments: list[Experiment]) -> Insight:
        return _unavailable(question, "AI integration")


class UnavailableResearchAssistant:
    def ask(
        self,
        question: str,
        experiment_ids: list[str] | None = None,
        validated_findings: list[dict[str, Any]] | None = None,
        top_k: int = 5,
    ) -> Insight:
        return _unavailable(question, "research assistant (RAG)")
