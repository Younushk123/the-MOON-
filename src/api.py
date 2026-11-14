"""Backend Handoff API module for NASA Spacecraft Fire Safety RAG.

Provides:
- callable function: answer_question(query: str, top_k: int = 5) -> dict
- FastAPI app exposing:
  - POST /ask
  - GET  /health
  - GET  /sources
  - POST /api/v1/assistant/ask (mounted team router from src.api_adapter)
"""
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from src.config import Settings
from rag_pipeline import NASARAG
from src.api_adapter import ask_research, build_router

_RAG_INSTANCE: Optional[NASARAG] = None


def get_rag(settings: Optional[Settings] = None, mode: str = "auto", use_semantic: bool = True) -> NASARAG:
    """Return a cached singleton NASARAG instance."""
    global _RAG_INSTANCE
    if _RAG_INSTANCE is None:
        _RAG_INSTANCE = NASARAG(settings=settings, mode=mode, use_semantic=use_semantic)
    return _RAG_INSTANCE


def answer_question(query: str, top_k: int = 5, rag: Optional[NASARAG] = None) -> Dict[str, Any]:
    """Callable RAG function for Backend / AI integration.

    Returns:
      query: original question
      claim: synthesized answer or abstention claim
      sources: list of source IDs cited in evidence or retrieved
      evidence: list of supporting evidence passages with chunk ID, page, text
      conditions: experimental conditions or limits
      abstained: boolean status indicating whether the system abstained
      data_status: data status classification
      evidence_status: supported | partially_supported | insufficient_evidence
      fire_safety_relevance: spacecraft fire safety relevance statement
      limitations: gaps, uncertainties, and constraints
      retrieval: retrieved chunks with scores and modes
      generation_mode: mode of generation (groq or extractive-offline)
      retrieval_mode: retrieval pipeline mode
      validation: verbatim quote and citation validation report
    """
    if not query or not query.strip():
        return {
            "query": query,
            "claim": "No question provided.",
            "sources": [],
            "evidence": [],
            "conditions": "N/A",
            "abstained": True,
            "data_status": "Insufficient Evidence",
            "evidence_status": "insufficient_evidence",
            "fire_safety_relevance": "N/A",
            "limitations": "Empty query provided.",
            "retrieval": [],
            "generation_mode": "none",
            "retrieval_mode": "none",
            "validation": {"ok": False, "problems": ["empty query"]},
            "warnings": ["Query string was empty."]
        }

    active_rag = rag or get_rag()
    res = ask_research(active_rag, query.strip(), top_k=top_k)

    # Collect source IDs from supporting evidence or top retrieved items
    cited_sources = []
    seen = set()
    for ev in res.get("supporting_evidence", []):
        sid = ev.get("source_id") or ev.get("register_id")
        if sid and sid not in seen:
            seen.add(sid)
            cited_sources.append(sid)
    if not cited_sources:
        for r in res.get("retrieved", [])[:3]:
            rid = r.get("register_id")
            if rid and rid not in seen:
                seen.add(rid)
                cited_sources.append(rid)

    return {
        "query": query,
        "claim": res["claim"],
        "sources": cited_sources,
        "evidence": res["supporting_evidence"],
        "conditions": res["experiment_conditions"],
        "abstained": res["abstained"],
        "data_status": res["data_status"],
        "evidence_status": res["evidence_status"],
        "fire_safety_relevance": res["fire_safety_relevance"],
        "limitations": res["limitations"],
        "retrieval": res["retrieved"],
        "generation_mode": res["generation_mode"],
        "retrieval_mode": res["retrieval_mode"],
        "validation": res["validation"],
        "warnings": res.get("warnings", [])
    }


# ================= FastAPI Application =================
app = FastAPI(
    title="NASA Spacecraft Fire Safety RAG Service",
    description="Evidence-grounded RAG API for microgravity combustion and fire safety research.",
    version="1.0.0"
)


class AskRequest(BaseModel):
    query: Optional[str] = Field(default=None, description="User question")
    question: Optional[str] = Field(default=None, description="Alias for query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    experiment_ids: Optional[List[str]] = Field(default=None, description="Optional PSI experiment IDs")
    validated_findings: Optional[List[Dict[str, Any]]] = Field(default=None, description="External findings pass-through")


class AskResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str
    error_code: Optional[str] = None


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(req: AskRequest):
    q = (req.query or req.question or "").strip()
    if not q:
        return AskResponse(
            success=False,
            data=None,
            message="Query cannot be empty.",
            error_code="EMPTY_QUERY"
        )
    try:
        data = answer_question(q, top_k=req.top_k)
        return AskResponse(
            success=True,
            data=data,
            message="Query answered successfully."
        )
    except Exception as e:
        return AskResponse(
            success=False,
            data=None,
            message=f"Processing error: {type(e).__name__}",
            error_code="RAG_ERROR"
        )


@app.get("/health")
def health_endpoint():
    rag = get_rag()
    return {
        "status": "healthy",
        "retrieval_mode": rag.retriever.mode,
        "generation_mode": rag.generator.mode,
        "total_chunks": len(rag.chunks),
        "total_sources": len(rag.register),
        "semantic_available": rag.retriever.semantic_available
    }


@app.get("/sources")
def sources_endpoint():
    rag = get_rag()
    sources_list = []
    for sid, entry in sorted(rag.register.items()):
        sources_list.append({
            "source_id": sid,
            "title": entry.title,
            "publisher": entry.publisher,
            "year": entry.year,
            "source_type": entry.source_type,
            "identifier": entry.identifier,
            "url": entry.url,
            "downloaded": entry.downloaded,
            "indexed_document": entry.indexed_document,
            "source_url_verified": "unverified",
            "specific_claims_verified": "unverified",
            "raw_data_available": "unverified/no",
            "origin": entry.origin
        })
    return {
        "total": len(sources_list),
        "sources": sources_list
    }


# Include existing team router for compatibility with POST /api/v1/assistant/ask
app.include_router(build_router(get_rag()))
