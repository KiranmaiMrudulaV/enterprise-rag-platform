from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """All ORM models inherit from this. Alembic uses it for autogenerate."""

    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields a DB session, closes it when the request completes."""
    async with AsyncSessionLocal() as session:
        yield session
