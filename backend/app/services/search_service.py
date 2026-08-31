import time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.generation.answer_parser import AnswerParser
from app.core.generation.llm_client import LLMClient
from app.core.generation.prompt_builder import PromptBuilder
from app.core.retrieval.retriever import Retriever
from app.db.models.chunk import Chunk
from app.db.models.document import Document
from app.db.models.search_history import SearchHistory
from app.schemas.search import Citation, SearchHistoryItem, SearchRequest, SearchResponse

RELATED_DOCS_MESSAGE = (
    "I don't have a confident answer to that in the available documents. "
    "Here are the most closely related passages I could find:"
)


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(self, request: SearchRequest) -> SearchResponse:
        start = time.time()

        retriever = Retriever()
        retrieved = retriever.retrieve(request.query, top_k=request.top_k)
        low_confidence = retriever.is_low_confidence(retrieved)

        context_chunks, chunk_by_chroma_id = await self._enrich(retrieved)

        if low_confidence or not context_chunks:
            return await self._respond_related_docs(request, context_chunks, chunk_by_chroma_id, start)

        prompt = PromptBuilder().build(request.query, context_chunks)
        llm_response = await LLMClient().generate(prompt)

        answer_text, used_indices = AnswerParser().parse(llm_response["text"], len(context_chunks))

        citations = [
            Citation(
                chunk_index=idx + 1,
                document_name=context_chunks[idx]["document_name"],
                page_number=context_chunks[idx]["page_number"],
                text=context_chunks[idx]["text"],
                chroma_id=context_chunks[idx]["chroma_id"],
            )
            for idx in used_indices
        ]

        latency_ms = int((time.time() - start) * 1000)
        source_ids = [
            chunk_by_chroma_id[c["chroma_id"]].id for c in context_chunks if c["chroma_id"] in chunk_by_chroma_id
        ]

        history = SearchHistory(
            query=request.query,
            answer=answer_text,
            mode="answered",
            source_chunk_ids=source_ids,
            latency_ms=latency_ms,
            token_count=llm_response.get("token_count"),
        )
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(history)

        return SearchResponse(
            search_id=history.id,
            query=request.query,
            answer=answer_text,
            mode="answered",
            citations=citations,
            latency_ms=latency_ms,
            token_count=llm_response.get("token_count"),
        )

    async def _respond_related_docs(self, request, context_chunks, chunk_by_chroma_id, start) -> SearchResponse:
        """AI-05: low-confidence fallback — return related documents instead of forcing an answer."""
        citations = [
            Citation(
                chunk_index=i + 1,
                document_name=c["document_name"],
                page_number=c["page_number"],
                text=c["text"],
                chroma_id=c["chroma_id"],
            )
            for i, c in enumerate(context_chunks)
        ]
        latency_ms = int((time.time() - start) * 1000)
        source_ids = [
            chunk_by_chroma_id[c["chroma_id"]].id for c in context_chunks if c["chroma_id"] in chunk_by_chroma_id
        ]

        history = SearchHistory(
            query=request.query,
            answer=RELATED_DOCS_MESSAGE,
            mode="related_docs",
            source_chunk_ids=source_ids,
            latency_ms=latency_ms,
            token_count=None,
        )
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(history)

        return SearchResponse(
            search_id=history.id,
            query=request.query,
            answer=RELATED_DOCS_MESSAGE,
            mode="related_docs",
            citations=citations,
            latency_ms=latency_ms,
            token_count=None,
        )

    async def _enrich(self, retrieved: list[dict]) -> tuple[list[dict], dict]:
        """Joins ChromaDB results back to PostgreSQL metadata via chroma_id (the bridge column)."""
        if not retrieved:
            return [], {}

        chroma_ids = [r["chroma_id"] for r in retrieved]
        result = await self.db.execute(select(Chunk).where(Chunk.chroma_id.in_(chroma_ids)))
        chunk_by_chroma_id = {c.chroma_id: c for c in result.scalars().all()}

        doc_ids = {c.document_id for c in chunk_by_chroma_id.values()}
        doc_result = await self.db.execute(select(Document).where(Document.id.in_(doc_ids)))
        docs_by_id = {d.id: d for d in doc_result.scalars().all()}

        context_chunks = []
        for r in retrieved:
            chunk = chunk_by_chroma_id.get(r["chroma_id"])
            if not chunk:
                continue
            doc = docs_by_id.get(chunk.document_id)
            context_chunks.append(
                {
                    "chroma_id": chunk.chroma_id,
                    "text": chunk.text,
                    "document_name": doc.original_name if doc else "Unknown",
                    "page_number": chunk.page_number,
                }
            )

        return context_chunks, chunk_by_chroma_id

    async def get_history(self, limit: int, offset: int) -> tuple[list[SearchHistoryItem], int]:
        total = await self.db.scalar(select(func.count()).select_from(SearchHistory))
        result = await self.db.execute(
            select(SearchHistory).order_by(SearchHistory.created_at.desc()).limit(limit).offset(offset)
        )
        items = [SearchHistoryItem.model_validate(h) for h in result.scalars().all()]
        return items, total or 0
