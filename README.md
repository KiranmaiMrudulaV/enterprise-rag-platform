# Enterprise RAG Platform

An internal knowledge assistant: employees ask questions in plain English and get
answers grounded in and cited to the company's own documents — HR policies, runbooks,
product specs, meeting notes — instead of a generic LLM guess.

```
"What is the PTO policy?"
   → searches uploaded documents
   → retrieves the relevant passage
   → answers with a citation back to "HR_Policy.pdf, page 3"
```

Built end-to-end following the same SDLC a production AI team would use: problem
framing and requirements before any code, a written system design and Architecture
Decision Records before implementation, then an implementation that matches what was
designed. See [`docs/`](docs/) for the full trail — nothing in this repo was built
without a documented reason.

---

## How it works

```
Document (PDF/DOCX/TXT) ──▶ Parse ──▶ Chunk ──▶ Embed ──▶ ChromaDB (vectors)
                                                              │
Question ──▶ Embed ──▶ ─────────────────────────────────────▶│
                                                              ▼
                                              Retrieve top-k similar chunks
                                                              │
                                              Join to PostgreSQL for
                                              document name + page number
                                                              │
                                              Build numbered-context prompt
                                                              │
                                              Claude API generates a cited answer
                                                              │
                                              Parse [1][2] citations, return
```

Full diagrams and the reasoning behind every arrow: [`docs/system-design.md`](docs/system-design.md).

## Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | FastAPI (Python 3.11) | Async-native, auto-generated OpenAPI docs |
| Vector DB | ChromaDB | Zero infra for V1; swappable to Pinecone behind one interface |
| Relational DB | PostgreSQL 15 | Structured metadata, search history, chunk↔document bridge |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Local, free, no API dependency |
| LLM | Claude (`claude-sonnet-4-6`) | Answer generation with citation instructions |
| Frontend | React + TypeScript + Tailwind + Vite | Type-safe, matches the OpenAPI contract exactly |
| Infra | Docker Compose + Nginx | One-command startup, single origin (no CORS) |
| CI | GitHub Actions | black, ruff, mypy, pytest, tsc, eslint on every PR |

Rationale for every choice: [`docs/adr/`](docs/adr/) (5 Architecture Decision Records).

## Running it locally

```bash
cp backend/.env.example backend/.env
# then set ANTHROPIC_API_KEY in backend/.env

cd infrastructure
docker-compose up --build
```

- Frontend: http://localhost:80
- API docs (interactive): http://localhost:8000/docs
- Health check: http://localhost:8000/health

Run the database migration once the stack is up:
```bash
docker-compose exec backend alembic upgrade head
```

## Running the tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest -v          # unit tests — no database or Docker required
black --check app tests
ruff check app tests
```

```bash
cd frontend
npm install
npx tsc --noEmit
npx eslint src --ext ts,tsx
```

## Project documentation

This repo was built by following an explicit 8-phase process before writing
implementation code — the same process a production AI engineering team uses:

| Phase | Document |
|---|---|
| 01 — Problem Framing | [`docs/problem-framing.md`](docs/problem-framing.md) |
| 02 — Requirements | [`docs/requirements.md`](docs/requirements.md) |
| 03 — System Design | [`docs/system-design.md`](docs/system-design.md), [`docs/adr/`](docs/adr/) |
| 04 — API Contract & RFC | [`docs/rfc-001-rag-core.md`](docs/rfc-001-rag-core.md), [`docs/openapi.yaml`](docs/openapi.yaml) |

## Key design decisions

- **Two-pipeline architecture** — ingestion (async, background) and query
  (real-time) are independent flows sharing one embedding model.
- **Two databases, one bridge column** — PostgreSQL for structured metadata,
  ChromaDB for vectors, joined via `chunks.chroma_id`.
- **Clean Architecture** — API → Services → Core → Data, no layer skips
  another; Core logic (chunking, prompt building, citation parsing) is unit
  tested with zero database or HTTP dependency.
- **Adapter pattern for the vector store** — all code calls `VectorStore`,
  never `chromadb` directly, so a production migration to Pinecone touches
  one file.
- **Low-confidence fallback** — below a similarity threshold, the system
  returns related documents instead of forcing an answer from weak context.
- **Structured error envelope** — every API error returns
  `{error: {code, message, details}}` so the frontend can branch on a
  stable code rather than parsing English text.

## Roadmap

- **V1 (current):** upload, ingest, ask, cited answers, search history — done.
- **V2:** JWT auth, document collections with RBAC, hybrid search (BM25 +
  Reciprocal Rank Fusion), cross-encoder reranking, thumbs up/down feedback.
- **V3:** Jira, Confluence, SharePoint, and Slack integrations.
- **V4:** RAGAS evaluation dashboard, hallucination detection, continuous
  feedback-driven quality tracking.
