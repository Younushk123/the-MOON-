"""Hybrid retriever: BM25 (original implementation kept) + semantic (Chroma) + moderate entity boost.
All scores are normalised to 0..1 before fusion, so an entity match can nudge but never outrank a
clearly better textual match (the old +8.0 raw boost could)."""
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

from .entities import match_entities

# Queries that really ask about records/metadata; for these, catalogue chunks are legitimate evidence.
METADATA_Q = re.compile(r"\b(doi|licen[cs]e|identifier|psi-\d+|download\w*|catalog\w*|listing|record|dataset|register|repository|source id|version)\b", re.I)
CATALOGUE_FACTOR = 0.8     # catalogue chunks are short metadata summaries; they must not outrank real passages on content questions

STOP = set("a an the of in on for to and or is are was were be what which who how why when does do did "
           "with that this by from at as it its into than then there their about alone listing shown".split())


def tokenize(text: str) -> List[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9\-_]", " ", text.lower())
    return [t for t in cleaned.split() if len(t) > 1]


@dataclass
class Hit:
    chunk: object
    score: float
    bm25: float
    semantic: Optional[float]
    entity_boost: float


class HybridRetriever:
    def __init__(self, chunks, register, settings, embedder=None, vector_store=None, embed_error=None):
        self.chunks, self.register, self.s = chunks, register, settings
        self.k1, self.b = 1.5, 0.75
        self.embedder, self.store = embedder, vector_store
        self.semantic_available = embedder is not None and vector_store is not None
        self.semantic_error = None if self.semantic_available else (embed_error or "no embedder/vector store configured")
        self._build()
        if self.semantic_available:
            # Only add and compute embeddings if vector store is empty / missing chunks
            if self.store.col.count() < len(chunks):
                self.store.add(chunks, embedder.encode([f"{c.title}. {c.content}" for c in chunks]))

    @property
    def mode(self) -> str:
        return "hybrid (BM25 + semantic + entity)" if self.semantic_available else \
            f"BM25 + entity ONLY - semantic retrieval NOT active ({self.semantic_error})"

    def _doc_tokens(self, c):
        meta = " ".join(str(v) for k, v in (c.metadata or {}).items() if k in ("publisher", "doi", "year", "identifier"))
        return tokenize(f"{c.title} {meta} {c.content} {c.register_id}")

    def _build(self):
        self.N = len(self.chunks)
        self.tf, self.dl, self.df = [], [], defaultdict(int)
        for c in self.chunks:
            toks = self._doc_tokens(c)
            self.dl.append(len(toks)); cnt = Counter(toks); self.tf.append(cnt)
            for t in cnt: self.df[t] += 1
        self.avgdl = sum(self.dl) / max(self.N, 1)

    def _idf(self, t):
        n = self.df.get(t, 0)
        return math.log(1.0 + (self.N - n + 0.5) / (n + 0.5))

    def _bm25(self, q_tokens) -> List[float]:
        out = []
        for i in range(self.N):
            s = 0.0
            for t in q_tokens:
                f = self.tf[i].get(t, 0)
                if f:
                    s += self._idf(t) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.dl[i] / self.avgdl))
            out.append(s)
        return out

    def retrieve(self, query: str, top_k: Optional[int] = None, focus_ids=None) -> List[Hit]:
        top_k = top_k or self.s.top_k
        q_tokens = [t for t in tokenize(query) if t not in STOP]
        raw = self._bm25(q_tokens)
        mx = max(raw) or 1.0
        bm = [r / mx for r in raw]
        sem: Dict[str, float] = {}
        if self.semantic_available:
            qv = self.embedder.encode([query])[0]
            sem = dict(self.store.query(qv, max(top_k * 4, 20)))
        ids, _labels = match_entities(query, self.register)
        ids = set(ids) | set(focus_ids or [])      # focus_ids = register IDs for requested experiment_ids (soft boost, not a hard filter)
        w_b, w_s = (self.s.w_bm25, self.s.w_semantic) if self.semantic_available else (1.0, 0.0)
        hits = []
        meta_q = bool(METADATA_Q.search(query))
        for i, c in enumerate(self.chunks):
            sv = sem.get(c.chunk_id) if self.semantic_available else None
            sv_n = max(0.0, sv) if sv is not None else 0.0
            boost = self.s.entity_boost if (c.register_id in ids or c.source_id in ids) else 0.0
            lex_sem = w_b * bm[i] + w_s * sv_n
            if c.content_type == "catalogue_record" and not meta_q:
                lex_sem *= CATALOGUE_FACTOR
            hits.append(Hit(c, lex_sem + boost, raw[i], sv, boost))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]
