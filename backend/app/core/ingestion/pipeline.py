"""
IngestionPipeline — orchestrates the full ingestion flow (system-design.md, section 1).

This is the only place parsers, chunker, embedder, and VectorStore are wired
together. document_service.py calls this; nothing else needs to know the
sequence of steps.
"""

import uuid

from app.config import settings
from app.core.ingestion.chunker import chunk_text
from app.core.ingestion.embedder import Embedder
from app.core.ingestion.parsers import parse_document
from app.db.vector_store import VectorStore


class IngestionPipeline:
    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = VectorStore()

    def run(self, file_path: str, document_id: str, file_type: str) -> list[dict]:
        """
        Returns a list of chunk dicts ready to persist as Chunk rows:
        [{"chroma_id", "chunk_index", "text", "page_number", "char_start",
          "char_end", "token_count"}]
        """
        pages = parse_document(file_path, file_type)

        all_chunks: list[dict] = []
        global_index = 0
        for page in pages:
            for chunk in chunk_text(
                page["text"],
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
                page_number=page["page_number"],
            ):
                chunk["chunk_index"] = global_index
                chunk["chroma_id"] = str(uuid.uuid4())
                all_chunks.append(chunk)
                global_index += 1

        if not all_chunks:
            return []

        texts = [c["text"] for c in all_chunks]
        vectors = self.embedder.embed_batch(texts)

        self.vector_store.upsert(
            [
                {
                    "chroma_id": c["chroma_id"],
                    "embedding": vectors[i],
                    "text": c["text"],
                    "document_id": document_id,
                    "page_number": c["page_number"],
                }
                for i, c in enumerate(all_chunks)
            ]
        )

        return all_chunks
