"""Adapter connecting the NASA RAG module to the backend ResearchAssistant."""

import sys
from functools import lru_cache
from pathlib import Path

# Locate the RAG project root.
RAG_ROOT = Path(__file__).resolve().parents[4]

if str(RAG_ROOT) not in sys.path:
    sys.path.insert(0, str(RAG_ROOT))


@lru_cache(maxsize=1)
def _load_rag():
    """Initialize the RAG engine once and reuse it."""
    from rag_pipeline import NASARAG

    return NASARAG(mode="auto")


class NASAResearchAssistant:
    """Backend-compatible wrapper around the RAG research assistant."""

    def ask(self, question: str):
        from src.api_adapter import ask_research

        from app.ids import new_id
        from app.models.insight import Evidence, Insight

        rag = _load_rag()
        result = ask_research(rag, question)

        evidence = [
            Evidence(
                source_id=item["source_id"],
                experiment_id=item.get("experiment_id"),
                evidence_text=item["evidence_text"],
                url=item.get("url"),
            )
            for item in result["supporting_evidence"]
            if item.get("source_id") and item.get("evidence_text")
        ]

        return Insight(
            insight_id=new_id("INSIGHT"),
            question=question,
            claim=result["claim"],
            supporting_evidence=evidence,
            fire_safety_relevance=result.get("fire_safety_relevance"),
            limitations=(
                [result["limitations"]]
                if isinstance(result.get("limitations"), str)
                else result.get("limitations") or []
            ),
            confidence="not_assessed",
            evidence_status=result["evidence_status"],
        )