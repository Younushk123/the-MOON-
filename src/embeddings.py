"""Sentence-transformers wrapper. Never fails silently: availability + reason are reported."""
from typing import List, Optional, Tuple


class Embedder:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.name = model_name

    def encode(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


def load_embedder(model_name="all-MiniLM-L6-v2") -> Tuple[Optional[Embedder], Optional[str]]:
    """Return (embedder, None) or (None, reason). Caller must surface the reason."""
    try:
        return Embedder(model_name), None
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:200]}"
