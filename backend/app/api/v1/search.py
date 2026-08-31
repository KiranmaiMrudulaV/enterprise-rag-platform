from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.search import PaginatedSearchHistory, SearchRequest, SearchResponse
from app.services.search_service import SearchService

router = APIRouter()


@router.post("", response_model=SearchResponse)
async def search(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    """
    The core RAG endpoint (system-design.md, section 9):
    embed -> retrieve -> enrich -> prompt -> generate -> parse citations -> persist.
    """
    service = SearchService(db)
    return await service.search(request)


@router.get("/history", response_model=PaginatedSearchHistory)
async def get_search_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    service = SearchService(db)
    items, total = await service.get_history(limit, offset)
    return PaginatedSearchHistory(items=items, total=total, limit=limit, offset=offset)
