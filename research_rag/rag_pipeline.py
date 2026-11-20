"""NASA microgravity combustion RAG - entry point.

  python rag_pipeline.py ingest                 # ingest PDFs/DOCX in data/raw_documents (needs manifest.json)
  python rag_pipeline.py ask "your question" [--mode groq|extractive|auto]
  (evaluation harness for T1-T30: NOT written yet)
The original hand-written seed (source IDs, chunk summaries, T1-T24) is preserved in src/legacy_seed.py.
"""
import argparse
import sys

from src.config import Settings
from src.embeddings import load_embedder
from src.generator import ExtractiveGenerator, GroqGenerator
from src.ingestion import ingest_directory
from src.retrieval import HybridRetriever
from src.source_register import build_corpus
from src.vector_store import VectorStore


class NASARAG:
    def __init__(self, settings=None, mode="auto", use_semantic=True):
        self.s = settings or Settings()
        self.register, self.chunks = build_corpus(self.s)
        embedder, err, store = None, "semantic retrieval disabled by caller", None
        if use_semantic:
            embedder, err = load_embedder(self.s.embed_model)
            if embedder:
                try:
                    store = VectorStore(self.s.processed_dir / "chroma")
                except Exception as e:
                    embedder, err = None, f"ChromaDB unavailable: {e!r}"[:200]
        self.retriever = HybridRetriever(self.chunks, self.register, self.s, embedder, store, err)
        if mode == "auto":
            mode = "groq" if self.s.groq_api_key else "extractive"
        self.generator = GroqGenerator(self.register, self.s) if mode == "groq" else ExtractiveGenerator(self.register, self.s)

    def ask(self, question, top_k=None):
        hits = self.retriever.retrieve(question, top_k)
        return hits, self.generator.generate(question, hits)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ingest")
    c = sub.add_parser("chat"); c.add_argument("--mode", default="auto")
    a = sub.add_parser("ask"); a.add_argument("question"); a.add_argument("--mode", default="auto")
    a.add_argument("--top-k", type=int, default=5)
    args = ap.parse_args()
    s = Settings()
    if args.cmd == "ingest":
        print(ingest_directory(s.raw_dir, s.processed_dir, s.chunk_words, s.chunk_overlap)); return
    rag = NASARAG(s, args.mode)
    if args.cmd == "chat":
        print(f"[retrieval] {rag.retriever.mode}\n[generation] {rag.generator.mode}\nType a question (empty line to quit).")
        while True:
            q = input("\nQ> ").strip()
            if not q:
                break
            _, res = rag.ask(q)
            print("\n" + res.answer.format_output())
        return
    print(f"[retrieval] {rag.retriever.mode}\n[generation] {rag.generator.mode}\n")
    hits, res = rag.ask(args.question, args.top_k)
    print(res.answer.format_output())
    if not res.validation.ok:
        print("VALIDATION PROBLEMS:", res.validation.problems)


if __name__ == "__main__":
    main()
