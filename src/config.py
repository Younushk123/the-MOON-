"""Central settings. Secrets come from the environment / .env only."""
import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")   # always the project-root .env, whatever the cwd
except Exception:  # python-dotenv optional
    pass

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    raw_dir: Path = ROOT / "data" / "raw_documents"
    processed_dir: Path = ROOT / "data" / "processed"
    workbook_path: Path = ROOT / "Investigation_Retrieval_Tests_Clean.xlsx"
    chunk_words: int = 180
    chunk_overlap: int = 30
    top_k: int = 5
    w_bm25: float = 0.5
    w_semantic: float = 0.5
    entity_boost: float = 0.25      # added to a 0..1 fused score, not a raw BM25 score
    min_coverage: float = 0.35      # share of distinctive query terms found in retrieved evidence
    embed_model: str = "all-MiniLM-L6-v2"
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    groq_api_key: str | None = field(default_factory=lambda: os.getenv("GROQ_API_KEY"), repr=False)
