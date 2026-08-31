import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class Citation(BaseModel):
    chunk_index: int
    document_name: str
    page_number: int | None
    text: str
    chroma_id: str


class SearchResponse(BaseModel):
    search_id: uuid.UUID
    query: str
    answer: str
    mode: str  # "answered" | "related_docs" — AI-05
    citations: list[Citation]
    latency_ms: int
    token_count: int | None


class SearchHistoryItem(BaseModel):
    id: uuid.UUID
    query: str
    answer: str | None
    latency_ms: int | None
    feedback: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedSearchHistory(BaseModel):
    items: list[SearchHistoryItem]
    total: int
    limit: int
    offset: int
