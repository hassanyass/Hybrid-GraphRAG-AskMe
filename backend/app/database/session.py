"""
Database session management.

Provides the async SQLAlchemy engine, session factory, and FastAPI
dependency for injecting database sessions into route handlers.

All database credentials are loaded from environment variables — no
hard-coded values.
"""

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _build_database_url() -> str:
    """
    Build the async database URL from environment variables.

    Supports either a single DATABASE_URL variable or individual
    POSTGRES_* variables. The async driver (asyncpg) is enforced.

    Returns:
        Async-compatible PostgreSQL connection string.

    Raises:
        ValueError: If required database configuration is missing.
    """
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Ensure the URL uses the async driver
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return database_url

    # Build from individual variables
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DATABASE")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")

    if not all([host, database, user, password]):
        raise ValueError(
            "Database configuration is incomplete. "
            "Provide either DATABASE_URL or all POSTGRES_* variables "
            "(POSTGRES_HOST, POSTGRES_DATABASE, POSTGRES_USER, POSTGRES_PASSWORD)."
        )

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"


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
