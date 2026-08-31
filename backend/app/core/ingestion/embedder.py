"""
Embedder — wraps the embedding model so it can be swapped (local -> API-based)
without touching any calling code. AI-12 (requirements.md) is enforced here:
this is the ONLY place an embedding model is loaded, used by both the
ingestion pipeline and the query-time retriever, guaranteeing they never drift apart.
"""

from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def _get_model():
    """Loaded once per process — sentence-transformers models are expensive to initialize."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


class Embedder:
    def __init__(self):
        self.model = _get_model()
        self.dimension = settings.embedding_dimension

    def embed(self, text: str) -> list[float]:
        """Single text -> vector. Used for embedding a user's query."""
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embedding — used during ingestion so chunks are encoded together, not one at a time."""
        if not texts:
            return []
        vectors = self.model.encode(texts, normalize_embeddings=True, batch_size=32)
        return [v.tolist() for v in vectors]
