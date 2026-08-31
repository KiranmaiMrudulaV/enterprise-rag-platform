"""
Retriever — embeds a query and returns the top-k most similar chunks.

Uses the same Embedder as ingestion (AI-12) and the VectorStore adapter
(ADR-002), so this file has zero knowledge of ChromaDB specifically.
"""

from app.config import settings
from app.core.ingestion.embedder import Embedder
from app.db.vector_store import VectorStore


class Retriever:
    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = VectorStore()

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
        """Returns [{"chroma_id", "text", "score", "document_id", "page_number"}], best first."""
        query_vector = self.embedder.embed(query)
        return self.vector_store.search(query_vector, top_k=top_k or settings.retrieval_top_k)

    def is_low_confidence(self, retrieved: list[dict]) -> bool:
        """AI-05: below this similarity threshold, the caller should fall back to related-docs mode."""
        if not retrieved:
            return True
        return retrieved[0]["score"] < settings.low_confidence_threshold
