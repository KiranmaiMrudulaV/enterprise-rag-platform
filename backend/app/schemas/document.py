import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    original_name: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentStatusResponse(BaseModel):
    id: uuid.UUID
    status: str
    error_message: str | None = None

    model_config = {"from_attributes": True}


class PaginatedDocuments(BaseModel):
    items: list[DocumentResponse]
    total: int
    limit: int
    offset: int
