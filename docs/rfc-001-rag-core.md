# RFC-001: Core RAG Pipeline — API Contract & Technical Specification

**Status:** Accepted
**Phase:** 04 — Technical Specification
**Depends on:** requirements.md, system-design.md, ADR-001 through ADR-005

---

## Problem Statement

Phases 01–03 established what the system does and how its components fit together.
Before writing implementation code, the API surface must be fully specified — every
endpoint, request shape, response shape, and error case — so the contract is fixed
and testable before it is built.

## Proposed Solution

A REST API under `/api/v1`, documented below, backed by the Clean Architecture layers
from `system-design.md`. Three cross-cutting conventions apply to every endpoint:

### Convention 1 — Pagination: offset/limit
```
GET /api/v1/search/history?limit=20&offset=0
→ { "items": [...], "total": 187, "limit": 20, "offset": 0 }
```
Chosen over cursor-based pagination because the deep-pagination performance problem
(DB scanning and discarding rows before an offset) only becomes material at row counts
far beyond this project's target scale (NFR-04: 500 documents). Cursor-based pagination
is the correct choice past that scale — noted here as the documented upgrade path.

### Convention 2 — JSON casing: snake_case
```json
{ "document_id": "abc-123", "chunk_count": 42, "created_at": "2026-01-01T00:00:00Z" }
```
Matches Pydantic's default serialization exactly — zero alias configuration needed on
any schema, ever. TypeScript interfaces on the frontend mirror this directly.

### Convention 3 — Error envelope
Every non-2xx response follows this shape:
```json
{ "error": { "code": "DOCUMENT_NOT_FOUND", "message": "No document found with id 'abc-123'.", "details": null } }
```
`code` is a stable, machine-readable identifier the frontend switches on. `message` is
for humans and logs and can be reworded without breaking frontend logic. `details` carries
structured extras (e.g. field-level validation errors).

---

## API Contract — V1

### Documents

**`POST /api/v1/documents/upload`**
- Request: `multipart/form-data`, field `file` (PDF, DOCX, or TXT/MD, max 50MB)
- Response: `202 Accepted`
  ```json
  { "id": "uuid", "original_name": "HR_Policy.pdf", "status": "pending", "created_at": "..." }
  ```
- Errors: `400 UNSUPPORTED_FILE_TYPE`, `413 FILE_TOO_LARGE`

**`GET /api/v1/documents`**
- Query params: `limit` (default 20), `offset` (default 0)
- Response: `200 OK`
  ```json
  { "items": [ { "id", "original_name", "file_type", "status", "chunk_count", "created_at" } ], "total": 12, "limit": 20, "offset": 0 }
  ```

**`GET /api/v1/documents/{id}`**
- Response: `200 OK` — full document metadata
- Errors: `404 DOCUMENT_NOT_FOUND`

**`GET /api/v1/documents/{id}/status`**
- Response: `200 OK` — `{ "id": "uuid", "status": "pending|processing|ready|failed", "error_message": null }`
- Errors: `404 DOCUMENT_NOT_FOUND`

**`DELETE /api/v1/documents/{id}`**
- Response: `204 No Content`
- Errors: `404 DOCUMENT_NOT_FOUND`
- Side effects: cascades to `chunks` rows (PostgreSQL) and vectors (ChromaDB)

### Search

**`POST /api/v1/search`**
- Request: `{ "query": "What is the PTO policy?", "top_k": 5 }`
- Response: `200 OK`
  ```json
  {
    "search_id": "uuid",
    "query": "What is the PTO policy?",
    "answer": "Employees receive 15 days PTO annually [1]...",
    "mode": "answered",
    "citations": [ { "chunk_index": 1, "document_name": "HR_Policy.pdf", "page_number": 3, "text": "...", "chroma_id": "..." } ],
    "latency_ms": 1240,
    "token_count": 512
  }
  ```
  `mode` is `"answered"` or `"related_docs"` — see AI-05 (low-confidence fallback).
- Errors: `400 EMPTY_QUERY`, `502 LLM_UNAVAILABLE`

**`GET /api/v1/search/history`**
- Query params: `limit`, `offset`
- Response: `200 OK` — paginated list of past queries (see pagination convention)

**`POST /api/v1/search/{id}/feedback`** — `[V2]`
- Request: `{ "rating": 1, "comment": "Optional text" }` (rating: `1` or `-1`)
- Response: `200 OK`

---

## Alternatives Considered

- **GraphQL instead of REST:** rejected — REST + auto-generated OpenAPI docs (free with
  FastAPI) gives equivalent discoverability with far less setup for a project this size.
- **Cursor pagination from day one:** rejected — see Convention 1. Documented as the
  explicit upgrade path if corpus size assumptions change.
- **RFC 7807 Problem Details for errors:** considered, but the custom envelope (Convention 3)
  gives the same machine-readable benefit with a simpler, project-specific shape. RFC 7807
  is noted here as the standardized alternative worth knowing for interviews.

## Open Questions

| # | Question | Resolved when |
|---|----------|---------------|
| 1 | Exact wording/taxonomy of all error codes | As each endpoint is implemented |
| 2 | Whether `/search` should support streaming responses (SSE) for perceived latency | V2 — noted as a UX upgrade, not required for V1 correctness |
