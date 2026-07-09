# Requirements
**Phase:** 02 — Requirements Gathering  
**Status:** Approved  
**Depends on:** [problem-framing.md](./problem-framing.md)

---

## Scope

This document defines what the system must do (Functional Requirements), how well it must do it
(Non-Functional Requirements), and the quality constraints specific to an AI system
(AI-Specific Requirements).

Requirements are versioned against delivery phases. A requirement tagged `[V1]` must be
satisfied before V1 ships. `[V2]` is a hard commitment for V2. `[V3+]` is acknowledged
but out of current scope.

---

## System Boundaries

**What is inside the system:**
- Document ingestion pipeline (PDF, DOCX, TXT/MD)
- Vector search and LLM-based question answering
- Citation rendering and source tracking
- Search history
- REST API consumed by the React frontend

**What is outside the system:**
- Real-time sync with Confluence, SharePoint, Notion — `[V3+]`
- Slack or Teams bot interface — `[V3+]`
- Multi-language document support — `[V3+]`
- Image, diagram, or table extraction from PDFs — `[V3+]`
- SSO / OAuth (enterprise identity providers) — `[V2]`

---

## Functional Requirements

These define **what** the system must do. A system that does not satisfy a `[V1]`
functional requirement is not shippable.

| ID | Requirement | Version | Notes |
|----|-------------|---------|-------|
| FR-01 | The system shall accept PDF file uploads | V1 | Via multipart HTTP POST |
| FR-02 | The system shall accept DOCX file uploads | V1 | Via multipart HTTP POST |
| FR-03 | The system shall accept plain text uploads (.txt, .md) | V1 | Via multipart HTTP POST |
| FR-04 | File uploads shall return immediately (202 Accepted) | V1 | Ingestion runs async in background |
| FR-05 | The system shall expose a status endpoint for ingestion progress | V1 | States: pending → processing → ready / failed |
| FR-06 | The system shall extract text and page numbers from uploaded documents | V1 | DOCX and TXT have no pages; page_number = null |
| FR-07 | The system shall split extracted text into overlapping chunks | V1 | Default: 512 tokens, 50-token overlap; configurable |
| FR-08 | The system shall generate a vector embedding for each chunk | V1 | Using sentence-transformers locally |
| FR-09 | The system shall store embeddings in a vector database | V1 | ChromaDB for V1 |
| FR-10 | The system shall store chunk metadata in a relational database | V1 | PostgreSQL: chunk text, page number, document id |
| FR-11 | The system shall accept a natural language query | V1 | Via POST /api/v1/search |
| FR-12 | The system shall return an answer grounded in retrieved document chunks | V1 | LLM answer, not free-form generation |
| FR-13 | Every answer shall include citations with document name and page number | V1 | Format: [1], [2] mapped to source metadata |
| FR-14 | When confidence is low, return related documents with a disclaimer | V1 | If top similarity score < 0.50, switch to related-docs mode |
| FR-15 | The system shall store every query and answer in search history | V1 | With latency_ms and token_count |
| FR-16 | The system shall allow users to delete a document | V1 | Removes from PostgreSQL and ChromaDB; cascades to chunks |
| FR-17 | The system shall list all documents with their processing status | V1 | Sorted by upload time, descending |
| FR-18 | Documents shall carry a version field in the schema | V1 | Schema-level support; full UI in V2 |
| FR-19 | Multiple versions of the same document shall be supported | V2 | Query always hits latest version by default |
| FR-20 | Users shall be able to query a specific document version | V2 | Version selector in UI |
| FR-21 | User authentication (email + password) | V2 | JWT access + refresh tokens |
| FR-22 | Document collections with role-based access | V2 | Roles: admin / user / viewer |
| FR-23 | Thumbs up / down feedback on every answer | V2 | Stored in search_history.feedback |

---

## Non-Functional Requirements

These define **how well** the system must perform. They are testable and measurable.

| ID | Requirement | Target | How Verified |
|----|-------------|--------|-------------|
| NFR-01 | Query end-to-end latency (p95) | < 2 seconds | Logged in search_history.latency_ms; load test in CI |
| NFR-02 | Ingestion latency for a 50-page PDF | < 60 seconds | Timed in integration test |
| NFR-03 | Maximum supported concurrent users | 50 | Async FastAPI handles this without tuning |
| NFR-04 | Maximum document corpus | 500 documents | ChromaDB local supports this comfortably |
| NFR-05 | Maximum file size per upload | 50 MB | Enforced at API layer |
| NFR-06 | System uptime | 99.5% monthly | Acceptable for V1 portfolio; SLA documented honestly |
| NFR-07 | Local deployment | Full stack runs via docker-compose up | Verified by clone + run |
| NFR-08 | No external dependencies at runtime (V1) | No cloud APIs required except the LLM | ChromaDB and Postgres run in Docker |
| NFR-09 | API documentation | Auto-generated, accessible at /docs | FastAPI provides this with no extra work |
| NFR-10 | Supported browsers | Chrome, Firefox, Safari (latest 2 versions) | Manual test on each |

---

## AI-Specific Requirements

These only apply to ML systems. They define the quality of the intelligence, not the software.
This is what separates an AI engineer from a web developer who used an LLM.

| ID | Requirement | Target | Priority | How Measured |
|----|-------------|--------|----------|-------------|
| AI-01 | Context Recall (RAGAS) | ≥ 0.70 | **CRITICAL** — primary constraint | RAGAS eval on golden dataset |
| AI-02 | Faithfulness (RAGAS) | ≥ 0.80 | High — grounding is a trust requirement | RAGAS eval on golden dataset |
| AI-03 | Answer Relevancy (RAGAS) | ≥ 0.75 | High — answer must address the question | RAGAS eval on golden dataset |
| AI-04 | Context Precision (RAGAS) | ≥ 0.65 | Medium — retrieval noise acceptable in V1 | RAGAS eval on golden dataset |
| AI-05 | Low-confidence threshold | similarity < 0.50 → related-docs mode | — | Configurable; set via env var |
| AI-06 | Hallucination rate | < 5% of queries | High — proxied by faithfulness < 0.50 | RAGAS faithfulness proxy |
| AI-07 | Cost per query | < $0.02 | Medium — tracked for scale awareness | token_count × model price per token |
| AI-08 | Chunk size | 512 tokens (configurable) | — | Environment variable CHUNK_SIZE |
| AI-09 | Chunk overlap | 50 tokens (configurable) | — | Environment variable CHUNK_OVERLAP |
| AI-10 | Retrieval top-k | 5 chunks (configurable) | — | Environment variable RETRIEVAL_TOP_K |
| AI-11 | Embedding model | all-MiniLM-L6-v2 for V1 | — | Consistent model across ingest and query |
| AI-12 | Same embedding model for ingestion and query | Enforced — same config value | **CRITICAL** | Mismatched models break all retrieval silently |

> **Why AI-01 (Context Recall) is marked CRITICAL:**
> Per the problem framing, coverage is the #1 system value. If a policy exists in the
> documents and the retriever fails to find it, the system has failed its core purpose.
> All tuning decisions prioritize recall before other metrics.
>
> **Why AI-12 is marked CRITICAL:**
> If the ingestion pipeline uses a different embedding model than the query pipeline,
> vectors will be in different spaces and cosine similarity will return garbage — no error,
> just silently wrong results. This is one of the most common production bugs in RAG systems.

---

## Data Requirements

| Item | Detail |
|------|--------|
| Document volume | Up to 500 documents in V1 |
| Chunk volume | ~100 chunks per 50-page PDF → up to ~50,000 chunks at max corpus |
| Vector dimension | 384 (all-MiniLM-L6-v2) |
| Estimated ChromaDB storage | ~50,000 chunks × 384 floats × 4 bytes ≈ 77 MB — well within local |
| Estimated Postgres storage | Chunk text (avg 300 chars × 50,000) ≈ 15 MB — trivial |
| Search history retention | All queries retained; no purge policy in V1 |

---

## Requirement Prioritization — MoSCoW

| Must Have (V1) | Should Have (V2) | Could Have (V3+) |
|----------------|------------------|------------------|
| PDF / DOCX / TXT ingestion | JWT auth + RBAC | Real-time Confluence sync |
| Async ingestion with status | Document versioning UI | Slack bot |
| Cited answers | Thumbs up/down feedback | Multi-language support |
| Low-confidence fallback | Analytics dashboard | Table/image extraction |
| Search history | Hybrid search (BM25 + semantic) | SSO / OAuth |
| Document delete | Cross-encoder reranker | SharePoint connector |

---

## Open Questions

| # | Question | Owner | Target |
|---|----------|-------|--------|
| 1 | What similarity score threshold maps to "low confidence" in practice? Set to 0.50 initially — validate against real queries in PoC phase. | Engineering | Phase 05 |
| 2 | Should .md files be chunked differently to preserve heading structure? (Heading-aware splitting could improve recall on structured docs) | Engineering | Phase 06 V1 |
| 3 | How many items in the golden evaluation dataset? Minimum 30 query-answer pairs across all user types. | Engineering | Phase 07 |
