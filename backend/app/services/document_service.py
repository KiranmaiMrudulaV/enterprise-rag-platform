import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import document_not_found
from app.core.ingestion.pipeline import IngestionPipeline
from app.db.database import AsyncSessionLocal
from app.db.models.chunk import Chunk
from app.db.models.document import Document
from app.db.vector_store import VectorStore

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def create_document(self, file: UploadFile, ext: str) -> Document:
        """Save the file to disk and create a Document row with status='pending'."""
        contents = await file.read()
        unique_filename = f"{uuid.uuid4()}.{ext}"
        storage_path = str(self.upload_dir / unique_filename)

        with open(storage_path, "wb") as f:
            f.write(contents)

        doc = Document(
            filename=unique_filename,
            original_name=file.filename,
            file_type=ext,
            file_size=len(contents),
            storage_path=storage_path,
            status="pending",
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def run_ingestion_pipeline(self, document_id: uuid.UUID) -> None:
        """
        Background task (ADR-003). Uses its own DB session because FastAPI's
        request-scoped session closes as soon as the HTTP response is sent.
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()
            if not doc:
                return

            doc.status = "processing"
            await session.commit()

            try:
                pipeline = IngestionPipeline()
                chunks_data = pipeline.run(doc.storage_path, str(doc.id), doc.file_type)

                for c in chunks_data:
                    session.add(
                        Chunk(
                            document_id=doc.id,
                            chroma_id=c["chroma_id"],
                            chunk_index=c["chunk_index"],
                            text=c["text"],
                            page_number=c.get("page_number"),
                            char_start=c.get("char_start"),
                            char_end=c.get("char_end"),
                            token_count=c.get("token_count"),
                        )
                    )

                doc.status = "ready"
                doc.chunk_count = len(chunks_data)
                await session.commit()

            except Exception as exc:  # noqa: BLE001 — ADR: capture and surface, never swallow silently
                doc.status = "failed"
                doc.error_message = str(exc)
                await session.commit()

    async def list_documents(self, limit: int, offset: int) -> tuple[list[Document], int]:
        total = await self.db.scalar(select(func.count()).select_from(Document))
        result = await self.db.execute(
            select(Document).order_by(Document.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total or 0

    async def get_document(self, document_id: uuid.UUID) -> Document:
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise document_not_found(str(document_id))
        return doc

    async def delete_document(self, document_id: uuid.UUID) -> None:
        doc = await self.get_document(document_id)

        VectorStore().delete_by_document(str(document_id))

        try:
            os.remove(doc.storage_path)
        except FileNotFoundError:
            pass

        await self.db.delete(doc)  # cascades to chunks via ON DELETE CASCADE
        await self.db.commit()
