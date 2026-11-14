"""Backend-facing adapter (team contract: POST /api/v1/assistant/ask).

Keeps RAG (documents/evidence) separate from structured data: validated findings produced by the Data Analysis
module can be passed in via `validated_findings`; they are returned verbatim, labelled with their origin, and are
NEVER mixed into the retrieved evidence or presented as RAG-sourced.

Pure function `ask_research()` is the integration point; a FastAPI router wraps it with the standard envelope.
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Settings
from .generator import DataStatus

TEAM_LABELS = {"official": "Official metadata verified",
               "download_listed": "Download listed; content not yet ingested",
               "ingested_checked": "Document ingested and checked",
               "insufficient": "Insufficient evidence"}


def _load_crosswalk(settings) -> Dict[str, str]:
    """S-id -> SRC-xxx. Empty until the team supplies the canonical list (we do not invent SRC ids)."""
    p = Path(settings.processed_dir).parent.parent / "source_register" / "crosswalk.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _experiment_map(rag) -> Dict[str, List[str]]:
    """PSI-xx -> register ids, from register identifiers (workbook Investigation Map)."""
    out: Dict[str, List[str]] = {}
    for sid, e in rag.register.items():
        for m in re.finditer(r"PSI-\d+", str(e.identifier), re.I):
            out.setdefault(m.group(0).upper(), []).append(sid)
    return out


def _team_status(res, hits_by_id, register) -> Dict[str, Any]:
    """Only assign a team label when the flag proving it exists; otherwise None + explanation."""
    if res.abstained:
        return {"label": TEAM_LABELS["insufficient"], "note": ""}
    chunks = [hits_by_id[c] for c in res.cited_chunk_ids if c in hits_by_id]
    if chunks and all(c.content_type == "document" and (c.metadata or {}).get("inspected") for c in chunks):
        return {"label": TEAM_LABELS["ingested_checked"], "note": ""}
    if chunks and all(c.content_type == "catalogue_record" and getattr(register.get(c.register_id), "url_verified", "") == "yes"
                      for c in chunks):
        return {"label": TEAM_LABELS["official"], "note": ""}
    return {"label": None, "note": "No manual verification flag on the cited sources (inspected / url_verified); "
                                   "cannot assign a team status label without it."}


def _evidence_status(res) -> str:
    if res.abstained:
        return "insufficient_evidence"
    return "supported" if res.answer.data_status == DataStatus.INDEXED_DOCUMENT else "partially_supported"


def ask_research(rag, question: str, experiment_ids: Optional[List[str]] = None,
                 validated_findings: Optional[List[Dict[str, Any]]] = None, top_k: int = 5) -> Dict[str, Any]:
    settings: Settings = rag.s
    xwalk = _load_crosswalk(settings)
    exp_map = _experiment_map(rag)
    focus, unknown = [], []
    for eid in experiment_ids or []:
        ids = exp_map.get(eid.upper())
        (focus.extend(ids) if ids else unknown.append(eid))
    hits = rag.retriever.retrieve(question, top_k, focus_ids=focus)
    res = rag.generator.generate(question, hits)
    by_id = {h.chunk.chunk_id: h.chunk for h in hits}
    evidence = []
    for cid in res.cited_chunk_ids:
        c = by_id.get(cid)
        if not c:
            continue
        line = next((l for l in res.answer.evidence.splitlines() if l.startswith(f"[{cid}]")), "")
        e = rag.register.get(c.register_id)
        evidence.append({
            "source_id": xwalk.get(c.register_id, c.register_id),       # SRC-xxx once crosswalk exists, else S-id
            "register_id": c.register_id,
            "experiment_id": next((k for k, v in exp_map.items() if c.register_id in v), None),
            "evidence_text": line.split("] ", 1)[1] if "] " in line else line,
            "chunk_id": cid, "page": c.page, "section": c.section, "content_type": c.content_type,
            "url": (e.url if e else None) or c.url,
            "title": c.title})
    ts = _team_status(res, by_id, rag.register)
    retrieved = [{"chunk_id": h.chunk.chunk_id, "register_id": h.chunk.register_id, "score": round(h.score, 4),
                  "bm25_raw": round(h.bm25, 3), "semantic": None if h.semantic is None else round(h.semantic, 4),
                  "content_type": h.chunk.content_type} for h in hits]
    warnings = []
    if unknown:
        warnings.append(f"No register record for experiment_ids {unknown}; they were ignored for retrieval focus.")
    if not rag.retriever.semantic_available:
        warnings.append("Semantic retrieval inactive: " + str(rag.retriever.semantic_error))
    if any(h.chunk.content_type == "seed_summary" for h in hits[:3]):
        warnings.append("Top results include unverified hand-written seed summaries, not original-document passages.")
    return {
        "question": question,
        "evidence_status": _evidence_status(res),            # supported | partially_supported | insufficient_evidence
        "abstained": res.abstained,
        "claim": res.answer.claim,
        "supporting_evidence": evidence,
        "nasa_source": res.answer.source,
        "experiment_conditions": res.answer.conditions,
        "fire_safety_relevance": res.fire_safety_relevance or "Not generated in this mode / not stated in retrieved evidence.",
        "limitations": res.answer.uncertainty,
        "data_status": res.answer.data_status.value,
        "team_status_label": ts["label"], "team_status_note": ts["note"],
        "validated_findings": validated_findings or [],      # passed through from Data Analysis; NOT RAG evidence
        "validated_findings_note": "Supplied by the Data Analysis module; not verified or modified by RAG." if validated_findings else "",
        "retrieved": retrieved,
        "generation_mode": res.mode, "retrieval_mode": rag.retriever.mode,
        "validation": {"ok": res.validation.ok, "problems": res.validation.problems},
        "warnings": warnings}


def build_router(rag):
    from fastapi import APIRouter
    from pydantic import BaseModel
    router = APIRouter(prefix="/api/v1/assistant")

    class AskRequest(BaseModel):
        question: str
        experiment_ids: Optional[List[str]] = None
        validated_findings: Optional[List[Dict[str, Any]]] = None
        top_k: int = 5

    @router.post("/ask")
    def ask(req: AskRequest):
        if not req.question.strip():
            return {"success": False, "data": None, "message": "Question is empty.", "error_code": "EMPTY_QUESTION"}
        try:
            data = ask_research(rag, req.question, req.experiment_ids, req.validated_findings, req.top_k)
        except Exception as e:      # never leak a stack trace into the envelope
            return {"success": False, "data": None, "message": f"RAG failure: {type(e).__name__}", "error_code": "RAG_ERROR"}
        return {"success": True, "data": data, "message": "Request completed successfully."}
    return router
