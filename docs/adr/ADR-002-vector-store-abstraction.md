# ADR-002: Abstract the vector store behind a VectorStore class

**Status:** Accepted  
**Date:** Phase 03 — System Design  
**Deciders:** Engineering

---

## Context

The system requires a vector database for similarity search. The V1 choice is ChromaDB
(runs in-process, no infrastructure). Production at scale will likely require Pinecone
or Weaviate (managed, horizontally scalable).

We need to decide: should application code import `chromadb` directly, or go through
an abstraction?

## Decision

All application code calls a `VectorStore` class in `app/db/vector_store.py`.
No file outside that module imports `chromadb` directly.

The `VectorStore` class exposes three methods:

```python
class VectorStore:
    def upsert(self, chunks: list[dict]) -> None
    def search(self, query_vector: list[float], top_k: int) -> list[dict]
    def delete_by_document(self, document_id: str) -> None
```

The implementation inside `vector_store.py` uses ChromaDB in V1.
Migrating to Pinecone means rewriting `vector_store.py` alone — zero other files change.

This is the **Adapter pattern**: our system depends on a stable interface, not a vendor.

## Consequences

**Positive:**
- Pinecone migration is a one-file change, not a search-and-replace across the codebase.
- Unit tests can inject a fake in-memory VectorStore without any running infrastructure.
- The interface makes ChromaDB's API differences from Pinecone invisible to the rest of the code.

**Negative:**
- One additional indirection. Developers must remember to use VectorStore, not chromadb directly.
- The abstraction is slightly leaky: ChromaDB and Pinecone have different consistency
  models and metadata filter syntaxes; complex queries may need interface changes at migration time.

## Alternatives Rejected

**Import chromadb directly everywhere:** Faster initially. Breaks when migrating to Pinecone —
every import site becomes a migration target. Also makes unit testing harder because you
can't swap in an in-memory fake without changing production code.
