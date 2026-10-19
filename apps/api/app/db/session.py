"""Database session management with SQLAlchemy 2 (async and sync)."""
from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Async engine for application operations
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    future=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Synchronous engine for Alembic migrations and utility scripts
sync_engine = create_engine(
    settings.DATABASE_SYNC_URL,
    echo=False,
    future=True,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
