"""
Base repository.

Provides a generic async CRUD repository that all domain-specific
repositories extend. This avoids duplicating standard data access
operations across every entity.
"""

import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic async CRUD repository.

    Subclasses must set ``model`` to their ORM class.

    Parameters:
        session: Active async database session (injected).
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> ModelT | None:
        """Retrieve a single entity by primary key."""
        return await self._session.get(self.model, entity_id)

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ModelT]:
        """Retrieve a paginated list of entities."""
        stmt = select(self.model).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, entity: ModelT) -> ModelT:
        """Insert a new entity and flush to obtain its generated fields."""
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(self, entity: ModelT) -> ModelT:
        """Merge updated entity state and flush."""
        merged = await self._session.merge(entity)
        await self._session.flush()
        await self._session.refresh(merged)
        return merged

    async def delete(self, entity: ModelT) -> None:
        """Remove an entity from the database."""
        await self._session.delete(entity)
        await self._session.flush()
