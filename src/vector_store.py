"""ChromaDB vector store. Embeddings are always supplied explicitly (Chroma's default embedder would
silently try to download its own model)."""
from typing import Dict, List, Tuple


class VectorStore:
    def __init__(self, path=None, collection="nasa_rag"):
        import chromadb
        self.client = chromadb.PersistentClient(path=str(path)) if path else chromadb.EphemeralClient()
        try:
            self.col = self.client.get_or_create_collection(collection, metadata={"hnsw:space": "cosine"})
        except Exception:
            try:
                self.client.delete_collection(collection)
            except Exception:
                pass
            self.col = self.client.create_collection(collection, metadata={"hnsw:space": "cosine"})

    def add(self, chunks, embeddings: List[List[float]]):
        self.col.upsert(ids=[c.chunk_id for c in chunks], embeddings=embeddings,
                        documents=[c.content for c in chunks],
                        metadatas=[{"register_id": c.register_id, "content_type": c.content_type} for c in chunks])

    def query(self, embedding: List[float], n: int) -> List[Tuple[str, float]]:
        r = self.col.query(query_embeddings=[embedding], n_results=min(n, self.col.count()))
        return [(i, 1.0 - d) for i, d in zip(r["ids"][0], r["distances"][0])]   # cosine sim
