# System Design
**Phase:** 03 — ML System Design  
**Status:** Approved  
**Depends on:** [requirements.md](./requirements.md)

---

## 1. The Two Pipelines

The entire system is built around two independent flows.
They share components (the Embedder) but are triggered separately and serve different purposes.

```
┌─────────────────────────────────────────────────────────────────┐
│  INGESTION PIPELINE  (triggered once per document, async)       │
│                                                                 │
│  User uploads file                                              │
│       │                                                         │
│       ▼                                                         │
│  [API Layer]  ── saves file to disk                             │
│               ── creates Document row (status = 'pending')      │
│               ── returns 202 Accepted + document_id             │
│               ── kicks off background task                      │
│       │                                                         │
│       ▼  (background, does not block HTTP)                      │
│  [Parser]     ── extracts text + page numbers from file         │
│       │          PDF: PyMuPDF  |  DOCX: python-docx             │
│       │          TXT/MD: plain read                             │
│       ▼                                                         │
│  [Chunker]    ── splits text into 512-token overlapping chunks  │
│       │          each chunk: text + chunk_index + page_number   │
│       ▼                                                         │
│  [Embedder]   ── converts each chunk text → 384-dim vector      │
│       │          model: all-MiniLM-L6-v2 (local, no API)        │
│       ▼                                                         │
│  [VectorStore]── upserts vectors into ChromaDB                  │
│       │          each entry: {chroma_id, embedding, text,       │
│       │                       metadata: {doc_id, page_num}}     │
│       ▼                                                         │
│  [DB Layer]   ── inserts Chunk rows in PostgreSQL               │
│               ── updates Document status = 'ready'              │
│               ── updates Document chunk_count                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  QUERY PIPELINE  (triggered on every user question, real-time)  │
│                                                                 │
│  User submits question: "What is the PTO policy?"               │
│       │                                                         │
│       ▼                                                         │
│  [API Layer]  ── validates request, calls SearchService         │
│       │                                                         │
│       ▼                                                         │
│  [Embedder]   ── converts question → 384-dim vector             │
│       │          MUST use the same model as ingestion           │
│       ▼                                                         │
│  [Retriever]  ── sends query vector to VectorStore              │
│       │          gets back top-5 chunks (by cosine similarity)  │
│       │                                                         │
│       │          if top score < 0.50 → related-docs mode        │
│       ▼                                                         │
│  [DB Layer]   ── fetches chunk metadata via chroma_id           │
│       │          gets: page_number, document.original_name      │
│       ▼                                                         │
│  [PromptBuilder]─ assembles numbered context:                   │
│       │          [1] Source: "HR_Policy.pdf", Page 3            │
│       │              "Employees get 15 days PTO..."             │
│       │          [2] Source: "Handbook.pdf", Page 12            │
│       │              "PTO accrues at 1.25 days/month..."        │
│       │          QUESTION: What is the PTO policy?              │
│       │          INSTRUCTION: cite as [1], [2]...               │
│       ▼                                                         │
│  [LLMClient]  ── calls Claude API, streams response             │
│       ▼                                                         │
│  [AnswerParser]─ extracts [1][2] markers from answer text       │
│       │          maps indices → chunk metadata                   │
│       ▼                                                         │
│  [DB Layer]   ── saves SearchHistory row                        │
│               ── stores query, answer, source_chunk_ids,        │
│               ── latency_ms, token_count                        │
│       ▼                                                         │
│  [API Layer]  ── returns:                                       │
│               ── {answer, citations:[{doc, page, text}],        │
│               ──  search_id, latency_ms, token_count}           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. The Bridge Pattern — how PostgreSQL and ChromaDB connect

This is the most important structural insight in the system.

ChromaDB stores vectors and returns IDs when you query. It knows nothing about document
names, page numbers, or users. PostgreSQL stores all that relational data but has no
concept of vector similarity.

The bridge is a single column: `chunks.chroma_id`.

```
  ChromaDB returns:              PostgreSQL knows:
  ┌─────────────────┐            ┌──────────────────────────────┐
  │ chroma_id: xyz  │──────────▶ │ chunks WHERE chroma_id='xyz' │
  │ score: 0.92     │            │   → page_number: 3           │
  │ text: "..."     │            │   → document_id: abc-123     │
  └─────────────────┘            │   → JOIN documents           │
                                 │     → original_name: HR.pdf  │
                                 └──────────────────────────────┘
```

When ChromaDB returns the top-5 chunks, the SearchService fetches their metadata from
PostgreSQL using the chroma_ids. That's how a citation goes from a raw vector result
to "HR_Policy.pdf, Page 3."

---

## 3. The Citation Mechanism — end to end

Citations are not magic. They are a prompt engineering + parsing pattern.

```
Step 1 — PromptBuilder numbers each chunk:
  [1] Source: "HR_Policy.pdf", Page 3
      "Full-time employees receive 15 days PTO annually..."
  [2] Source: "Benefits_Guide.pdf", Page 7
      "PTO accrues at 1.25 days per month..."

Step 2 — Claude's system instruction:
  "Answer using ONLY the context above.
   Cite every factual claim as [1], [2], etc.
   If context doesn't contain the answer, say so. Do not guess."

Step 3 — Claude responds:
  "Employees receive 15 days of PTO per year [1], accruing
   at 1.25 days per month starting from day one [2]."

Step 4 — AnswerParser extracts markers:
  used_indices = [0, 1]  (0-based: [1] → index 0, [2] → index 1)

Step 5 — SearchService maps indices to metadata:
  citations = [
    {chunk_index: 1, document_name: "HR_Policy.pdf", page_number: 3, text: "..."},
    {chunk_index: 2, document_name: "Benefits_Guide.pdf", page_number: 7, text: "..."},
  ]

Step 6 — Frontend renders [1] as a clickable badge.
  Clicking it shows the source passage in a side panel.
```

---

## 4. The Status State Machine — ingestion error handling

A Document has exactly one status at any time. The transitions are one-directional.

```
           upload received
                │
                ▼
           ┌─────────┐
           │ pending │  ← Document row created, file saved to disk
           └─────────┘
                │  background task starts
                ▼
         ┌────────────┐
         │ processing │  ← Parser + Chunker + Embedder running
         └────────────┘
          │           │
          │ success   │ failure (exception caught)
          ▼           ▼
       ┌───────┐  ┌────────┐
       │ ready │  │ failed │  ← error_message stored, partial chunks cleaned up
       └───────┘  └────────┘
                      │
                      │  user deletes and re-uploads corrected file
                      ▼
                  (new document_id, starts from 'pending')
```

The `failed` state is permanent. There is no automatic retry in V1. The user sees the error
message in the document list, deletes the document, fixes the file, and re-uploads.

---

## 5. Clean Architecture — the four layers

Every piece of code lives in exactly one layer. No layer skips another.

```
┌────────────────────────────────────────────────────┐
│  API LAYER  (app/api/)                             │
│  Knows about: HTTP, request validation, responses  │
│  Does NOT know about: ChromaDB, LLMs, chunking     │
│  Files: documents.py, search.py, auth.py           │
├────────────────────────────────────────────────────┤
│  SERVICE LAYER  (app/services/)                    │
│  Knows about: Core logic + DB models               │
│  Does NOT know about: HTTP, FastAPI, routing       │
│  Files: document_service.py, search_service.py     │
├────────────────────────────────────────────────────┤
│  CORE LAYER  (app/core/)                           │
│  Pure logic. No HTTP. No database.                 │
│  Does NOT know about: FastAPI, SQLAlchemy          │
│  Files: parsers, chunker, embedder, retriever,     │
│         prompt_builder, llm_client, answer_parser  │
├────────────────────────────────────────────────────┤
│  DATA LAYER  (app/db/)                             │
│  Knows about: PostgreSQL, ChromaDB                 │
│  Does NOT know about: HTTP, business logic         │
│  Files: database.py, models/, vector_store.py      │
└────────────────────────────────────────────────────┘
```

Why this matters for testing:
- You can unit test `chunker.py` with a plain string — no database, no HTTP server needed.
- You can unit test `prompt_builder.py` with fake chunks — no LLM call needed.
- You can integration test `search_service.py` with a real DB but a mocked LLM.
- You can E2E test the API with `httpx.AsyncClient` against the full stack.

---

## 6. The VectorStore Abstraction — Adapter Pattern

All application code calls `VectorStore`. Never `chromadb` directly.

```python
# What all other code sees (the interface):
class VectorStore:
    def upsert(self, chunks: list[dict]) -> None: ...
    def search(self, query_vector: list[float], top_k: int) -> list[dict]: ...
    def delete_by_document(self, document_id: str) -> None: ...

# V1: ChromaDB implements it internally.
# V2/prod: swap to Pinecone by changing this file alone.
# Tests: swap to an in-memory fake — no Docker needed to run unit tests.
```

This is the **Adapter pattern**: your system depends on a stable interface,
not on a specific vendor. When ChromaDB is replaced by Pinecone at scale,
zero files outside `vector_store.py` change.

---

## 7. Technology Decisions

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Backend framework | FastAPI | Async-native, auto-generates OpenAPI docs, Python is the AI/ML standard |
| Vector database (V1) | ChromaDB | Zero infrastructure, in-process, identical API surface to Pinecone for easy migration |
| Vector database (prod) | Pinecone | Managed, horizontally scalable, no ops burden |
| Relational database | PostgreSQL 15 | Standard, JSONB for flexible metadata, UUID support, ARRAY type for chunk id lists |
| Embedding model | all-MiniLM-L6-v2 | Runs locally (no API key needed), 384-dim, fast, good quality for English enterprise text |
| PDF parsing | PyMuPDF (fitz) | Preserves reading order better than pdfplumber, handles complex layouts |
| DOCX parsing | python-docx | Official library, stable |
| Token counting | tiktoken | Same tokenizer as Claude/GPT — accurate chunk sizing |
| LLM | Claude (claude-sonnet-4-6) | Strong instruction following for citation format, good context length |
| Frontend | React + TypeScript + Vite | TypeScript is non-negotiable at big tech; Vite is the modern build tool |
| Styling | Tailwind CSS | Utility-first, no context switching between files |
| State management | Zustand | Lighter than Redux, idiomatic for this scale |
| Containerization | Docker + docker-compose | One-command startup, portable across machines |
| Reverse proxy | Nginx | Routes /api/* → backend, /* → frontend; eliminates CORS |
| CI | GitHub Actions | Free for public repos, standard at all tech companies |

---

## 8. Component Map — one sentence per file

```
app/
├── main.py              ← FastAPI app, mounts router, CORS middleware
├── config.py            ← All env vars in one place (pydantic-settings)
│
├── api/v1/
│   ├── router.py        ← Aggregates all sub-routers into one
│   ├── documents.py     ← Upload, list, delete, status endpoints
│   ├── search.py        ← POST /search, GET /search/history
│   └── auth.py          ← Register, login, refresh [V2]
│
├── core/
│   ├── ingestion/
│   │   ├── parsers.py   ← PDF/DOCX/TXT → [{text, page_number}]
│   │   ├── chunker.py   ← text → [{text, chunk_index, page_num, token_count}]
│   │   ├── embedder.py  ← text → [float × 384]  (sentence-transformers wrapper)
│   │   └── pipeline.py  ← orchestrates parsers → chunker → embedder → vector_store
│   │
│   ├── retrieval/
│   │   ├── retriever.py ← query string → top-k chunk dicts from VectorStore
│   │   └── reranker.py  ← [V2] cross-encoder reranking of top-20 → top-5
│   │
│   └── generation/
│       ├── llm_client.py     ← Anthropic SDK wrapper, streaming
│       ├── prompt_builder.py ← assembles numbered context + citation instruction
│       └── answer_parser.py  ← extracts [1][2] indices from answer text
│
├── services/
│   ├── document_service.py  ← upload flow + ingestion pipeline orchestration
│   └── search_service.py    ← query flow: retrieve → enrich → prompt → generate → save
│
└── db/
    ├── database.py          ← SQLAlchemy async engine + session factory
    ├── models/              ← ORM: User, Document, Chunk, SearchHistory
    ├── vector_store.py      ← VectorStore class (ChromaDB adapter)
    └── migrations/          ← Alembic migration versions
```

---

## 9. Sequence Diagram — Query (detailed)

```
User        API           SearchService    Embedder    VectorStore   PostgreSQL    Claude API
 │           │                │               │             │             │             │
 │──POST /search──▶          │               │             │             │             │
 │           │──call search()─▶              │             │             │             │
 │           │               │──embed(query)─▶            │             │             │
 │           │               │               │─────────────────────────▶│             │
 │           │               │◀──[0.12,-0.45,...]─────────│             │             │
 │           │               │──search(vector, top_k=5)───▶             │             │
 │           │               │               │             │─────────────────────────▶│
 │           │               │               │             │◀──[{chroma_id, text, score}×5]
 │           │               │──SELECT chunks WHERE chroma_id IN (...)──▶             │
 │           │               │                             │◀──[{page_num, doc_name}×5]
 │           │               │──build_prompt(query, chunks)│             │             │
 │           │               │──call Claude API────────────────────────────────────────▶
 │           │               │◀──"...answer...[1][2]..."──────────────────────────────│
 │           │               │──parse_citations([1][2])   │             │             │
 │           │               │──INSERT search_history──────────────────▶│             │
 │           │◀──{answer, citations, latency_ms}──         │             │             │
 │◀──200 OK──│               │               │             │             │             │
```

---

## 10. What Changes Between V1 and V2

The architecture is designed so V2 additions slot in without modifying V1 code.

| V1 (complete) | V2 addition | What changes |
|---------------|-------------|--------------|
| No auth — all endpoints open | JWT middleware | `Depends(get_current_user)` added to each router; no logic changes |
| Single implicit collection | Collections table + RBAC | SearchService adds collection filter to VectorStore query |
| ChromaDB local | Pinecone (optional) | `vector_store.py` implementation swapped; interface unchanged |
| Semantic search only | Hybrid search (BM25 + RRF) | `retriever.py` gets a second search path; interface unchanged |
| No reranker | Cross-encoder reranker | `reranker.py` added between retriever and prompt_builder; no other changes |
