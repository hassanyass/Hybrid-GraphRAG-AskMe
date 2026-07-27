"""
Database session management.

Provides the async SQLAlchemy engine, session factory, and FastAPI
dependency for injecting database sessions into route handlers.

All database credentials are loaded from environment variables — no
hard-coded values.
"""

import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

load_dotenv(".env")


def _build_database_url() -> str:
    """
    Build the async database URL from environment variables.

    Expects a single DATABASE_URL environment variable, such as
    one provided by Supabase.

    Returns:
        Async-compatible PostgreSQL connection string.

    Raises:
        ValueError: If DATABASE_URL is missing.
    """
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set.")

    # Ensure the URL uses the async driver
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )
    return database_url


# ---------------------------------------------------------------------------
# Engine & Session Factory
# ---------------------------------------------------------------------------

DATABASE_URL = _build_database_url()

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true",
    pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
    pool_pre_ping=True,
    pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# FastAPI Dependency
# ---------------------------------------------------------------------------

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a transactional database session.

    Yields an AsyncSession and ensures it is closed after the request
    completes, regardless of success or failure.

    Usage::

        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
