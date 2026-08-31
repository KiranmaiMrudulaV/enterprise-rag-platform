"""
VectorStore — the Adapter pattern from ADR-002.

All application code calls THIS class. No file outside this module imports
`chromadb` directly. Migrating to Pinecone at production scale (ADR-005) means
rewriting only this file — every caller (retriever.py, document_service.py,
tests) keeps working unchanged because they depend on this interface, not on
ChromaDB's specific API shape.
"""

from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def _get_client():
    import chromadb

    return chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)


class VectorStore:
    def __init__(self):
        self.client = _get_client()
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, chunks: list[dict]) -> None:
        """
        chunks: [{"chroma_id": str, "embedding": list[float], "text": str,
                  "document_id": str, "page_number": int|None}]
        """
        if not chunks:
            return

        self.collection.upsert(
            ids=[c["chroma_id"] for c in chunks],
            embeddings=[c["embedding"] for c in chunks],
            documents=[c["text"] for c in chunks],
            metadatas=[
                {"document_id": c["document_id"], "page_number": c.get("page_number") or -1} for c in chunks
            ],
        )

    def search(self, query_vector: list[float], top_k: int = 5) -> list[dict]:
        """Returns [{"chroma_id", "text", "score", "document_id", "page_number"}], best match first."""
        results = self.collection.query(query_embeddings=[query_vector], n_results=top_k)

        if not results["ids"] or not results["ids"][0]:
            return []

        out = []
        for i, chroma_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]
            score = 1 - distance  # cosine distance -> similarity
            metadata = results["metadatas"][0][i]
            out.append(
                {
                    "chroma_id": chroma_id,
                    "text": results["documents"][0][i],
                    "score": score,
                    "document_id": metadata.get("document_id"),
                    "page_number": metadata.get("page_number") if metadata.get("page_number", -1) != -1 else None,
                }
            )
        return out

    def delete_by_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})
