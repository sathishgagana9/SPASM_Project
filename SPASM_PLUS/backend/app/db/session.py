"""
Async SQLAlchemy engine + session management.

Uses SQLite for development. DATABASE_URL is the single point of
change required to migrate to PostgreSQL later (e.g.
postgresql+asyncpg://user:pass@host/db) — no other application code
should assume SQLite.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create tables. Replace with Alembic migrations once the schema stabilizes."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
