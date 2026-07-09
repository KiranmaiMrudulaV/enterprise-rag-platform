# ADR-004: Chunk size 512 tokens with 50-token overlap

**Status:** Accepted  
**Date:** Phase 03 — System Design  
**Deciders:** Engineering

---

## Context

Every chunk must be small enough to produce a focused embedding but large enough
to contain complete thoughts. The overlap prevents important sentences being split
across two chunks and lost to retrieval.

Three competing concerns:
1. **Embedding quality** — smaller chunks produce more focused vectors; larger chunks dilute the signal.
2. **Context sufficiency** — the LLM needs enough text in the retrieved chunk to construct an answer.
3. **Retrieval noise** — very large chunks retrieved because of one matching sentence bring in many unrelated sentences.

## Decision

- **Chunk size: 512 tokens** (~350–400 words, approximately 2-3 paragraphs)
- **Overlap: 50 tokens** (~40 words)
- **Splitting strategy:** Recursive character splitting — tries paragraph breaks (`\n\n`), then sentence breaks (`. `), then word breaks (` `), then character. Preserves natural language boundaries.
- Both values are environment variables (`CHUNK_SIZE`, `CHUNK_OVERLAP`), enabling tuning without code changes.

**Rationale for 512:** Industry standard for English enterprise documents. Google's RAG
paper and LlamaIndex's default both converge around this range. Empirically: a 512-token
chunk is long enough to contain a complete policy clause, short enough to be about one topic.

**Rationale for 50-token overlap:** Roughly 10% of chunk size. This is the standard
recommendation. Larger overlap means the same text appears in many chunks (storage and
indexing waste). Smaller overlap risks losing sentences at boundaries.

## Planned V2 Upgrade: Hierarchical Chunking

In V2, implement "small-to-big" retrieval:
- Retrieve by small chunks (128 tokens) for precision
- Pass the parent large chunk (1024 tokens) to the LLM for context

This is also known as the "child-parent retrieval" pattern. It improves both
retrieval precision and answer quality.

## Consequences

**Positive:**
- Values are configurable — the PoC phase will validate whether 512/50 is optimal for our specific documents.
- Standard values mean comparison to published benchmarks is meaningful.

**Negative:**
- 512 tokens is not optimal for all document types. A highly structured runbook with
  short step-by-step items may benefit from smaller chunks (256). To be validated in Phase 05.

## Alternatives Rejected

**Fixed character splitting (e.g., every 2000 characters):** Faster to implement, but
splits on character count without regard for sentence or paragraph boundaries. Produces
chunks that start and end mid-sentence. Empirically worse retrieval quality.

**Sentence-level chunking:** Every sentence is its own chunk. Very precise but too short —
a single sentence rarely contains enough context for the LLM to answer from.
