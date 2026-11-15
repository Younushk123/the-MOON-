"""Run standalone:  uvicorn api:app --port 8001      (backend can also import src.api_adapter.ask_research directly)"""
from fastapi import FastAPI
from rag_pipeline import NASARAG
from src.api_adapter import build_router

rag = NASARAG(mode="auto")
app = FastAPI(title="THE MOON research_rag")
app.include_router(build_router(rag))


@app.get("/api/v1/assistant/health")
def health():
    return {"success": True, "data": {"retrieval_mode": rag.retriever.mode, "generation_mode": rag.generator.mode,
                                      "n_chunks": len(rag.chunks), "n_sources": len(rag.register)}, "message": "ok"}
