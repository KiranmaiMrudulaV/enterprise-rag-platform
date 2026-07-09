# ADR-003: Use async background ingestion with 202 Accepted

**Status:** Accepted  
**Date:** Phase 03 — System Design  
**Deciders:** Engineering

---

## Context

Ingesting a document involves: reading the file, extracting text page by page, splitting
into chunks, generating embeddings for each chunk (the slowest step), and writing to two
databases. For a 50-page PDF, this takes 20-60 seconds.

If the upload endpoint waits for ingestion to complete before responding, the HTTP request
will timeout on large files. Clients (browsers, API consumers) typically timeout after 30s.

## Decision

The upload endpoint returns **202 Accepted** immediately after:
1. Saving the file to disk
2. Creating a Document row with `status = 'pending'`

Ingestion runs as a **FastAPI BackgroundTask** — triggered after the response is sent.

The client polls `GET /api/v1/documents/{id}/status` until status becomes `ready` or `failed`.

The status state machine is: `pending → processing → ready | failed`

```
POST /upload        → 202 {document_id: "abc"}       (returns in < 100ms)
GET  /documents/abc/status → {status: "processing"}  (client polls every 2s)
GET  /documents/abc/status → {status: "ready"}        (ingestion complete)
```

## Consequences

**Positive:**
- No timeout risk regardless of document size or server load.
- Upload endpoint is fast — good UX for the user who uploaded.
- Status polling pattern is simple to implement on the frontend.
- Naturally supports V2 upgrade to Celery + Redis for distributed job queuing.

**Negative:**
- Client must implement polling. A WebSocket or Server-Sent Events approach would
  give real-time push notifications without polling, but adds complexity.
- If the server restarts mid-ingestion, the Document stays in `processing` forever.
  V1 mitigation: on startup, reset any documents stuck in `processing` to `failed`.

## Alternatives Rejected

**Synchronous ingestion (wait and return 200):** Simple but breaks on large files.
Browser timeout is typically 30s; a 100-page PDF can take 90s+ to embed.

**WebSockets for status push:** Better UX (no polling). Added significantly more complexity
to both backend and frontend. Deferred to V3.
