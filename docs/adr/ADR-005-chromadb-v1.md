# ADR-005: Use ChromaDB for vector storage in V1

**Status:** Accepted  
**Date:** Phase 03 — System Design  
**Deciders:** Engineering

---

## Context

The system requires a vector database. Requirements specify:
- Up to 500 documents, ~50,000 chunks (well within single-node limits)
- Local deployment via docker-compose (no cloud accounts required for V1)
- Must be swappable to Pinecone for production without architecture changes (ADR-002)

Evaluated options:

| Option | Infrastructure | Cost | Migration to prod |
|--------|---------------|------|------------------|
| ChromaDB | In-process or Docker | Free | Swap `vector_store.py` |
| Pinecone | Managed cloud | Paid (free tier limited) | Already prod |
| Weaviate | Self-hosted | Free, but ops burden | Swap `vector_store.py` |
| pgvector | PostgreSQL extension | Free | SQL query changes |

## Decision

Use **ChromaDB** running as a Docker service in V1.

Run it as a separate container (not in-process) so it persists across backend restarts
and more closely mirrors the production pattern (separate vector DB service).

## Consequences

**Positive:**
- Zero cost. No API key required for V1 development.
- docker-compose brings it up in one line — recruiters can clone and run with no accounts.
- The VectorStore abstraction (ADR-002) means migration to Pinecone is isolated.
- ChromaDB's API is well-documented and similar in structure to Pinecone's.

**Negative:**
- ChromaDB does not scale beyond a single node. Not suitable for production at scale.
- ChromaDB's consistency guarantees are weaker than Pinecone's.
- Does not support hybrid search natively — BM25 must be implemented separately in V2.

## Migration Plan (V2/prod)

When migrating to Pinecone:
1. Rewrite `app/db/vector_store.py` to use the Pinecone client.
2. Run a one-time re-ingestion script to populate Pinecone from existing PostgreSQL chunk data.
3. No other files change.

## Alternatives Rejected

**pgvector:** Keeps everything in one database (no ChromaDB container). However, pgvector
performance degrades without careful index tuning at scale, and using it would make the
architecture less representative of real-world RAG systems (which typically use a dedicated
vector DB). Also: mixing the vector index and the relational schema in one database
violates the two-database boundary principle, which is itself a valuable teaching point.
