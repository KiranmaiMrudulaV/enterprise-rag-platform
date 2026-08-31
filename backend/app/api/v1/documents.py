import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import file_too_large, unsupported_file_type
from app.db.database import get_db
from app.schemas.document import DocumentResponse, DocumentStatusResponse, PaginatedDocuments
from app.services.document_service import ALLOWED_EXTENSIONS, DocumentService

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Accepts a document, returns 202 immediately (ADR-003), and runs the
    parse -> chunk -> embed -> store pipeline as a background task.
    """
    ext = (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "").lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise unsupported_file_type(ext or "unknown")

    service = DocumentService(db)
    contents_preview = await file.read(settings.max_upload_size_mb * 1024 * 1024 + 1)
    if len(contents_preview) > settings.max_upload_size_mb * 1024 * 1024:
        raise file_too_large(settings.max_upload_size_mb)
    await file.seek(0)

    document = await service.create_document(file, ext)
    background_tasks.add_task(service.run_ingestion_pipeline, document.id)
    return document


@router.get("", response_model=PaginatedDocuments)
async def list_documents(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    items, total = await service.list_documents(limit, offset)
    return PaginatedDocuments(items=items, total=total, limit=limit, offset=offset)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = DocumentService(db)
    return await service.get_document(document_id)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Frontend polls this until status is 'ready' or 'failed' (ADR-003)."""
    service = DocumentService(db)
    doc = await service.get_document(document_id)
    return DocumentStatusResponse(id=doc.id, status=doc.status, error_message=doc.error_message)


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = DocumentService(db)
    await service.delete_document(document_id)
