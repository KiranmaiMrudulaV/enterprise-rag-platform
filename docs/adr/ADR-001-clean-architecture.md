# ADR-001: Adopt Clean Architecture with four strict layers

**Status:** Accepted  
**Date:** Phase 03 — System Design  
**Deciders:** Engineering

---

## Context

We need to decide how to organize the backend codebase. Two realistic options:
simple two-tier (routers + DB), or Clean Architecture (API → Services → Core → Data).

The system will grow from V1 (core RAG) through V4 (observability + integrations).
Each version adds components. Without a clear layering strategy, the codebase
becomes harder to extend and test as it grows.

## Decision

Adopt four strict layers with one rule: **no layer may skip another layer, and
no layer may depend on a layer above it.**

```
API      → Services → Core → Data
(HTTP)     (orchestration)  (DB/Vector)
             (pure logic)
```

Each layer is tested independently:
- Core components (chunker, embedder, prompt_builder) are tested with plain Python — no DB, no HTTP.
- Services are tested with a real DB but mocked LLM calls.
- API endpoints are tested with FastAPI's test client against the full stack.

## Consequences

**Positive:**
- Every component is independently replaceable. Swap ChromaDB to Pinecone: one file changes.
- Unit tests run without Docker (core layer has zero infrastructure dependencies).
- Interviewers can look at any file and immediately understand its responsibility.
- V2 additions (auth, collections) slot into the API layer without touching Core.

**Negative:**
- More files than a simple two-tier approach.
- New contributors must understand the layering rule before contributing.
- Some simple operations (e.g., a health check) feel over-engineered for four layers.

## Alternatives Rejected

**Simple two-tier (router + DB):** Faster to write initially, but business logic ends up
inside route handlers. Testing requires a running HTTP server and database for every test.
Logic becomes hard to find as the codebase grows. Does not demonstrate architectural
thinking to an interviewer.
