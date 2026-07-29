"""
Chunk repository.

Data access layer for DocumentChunk entities.
Provides efficient batch operations for pipeline processing.
"""

import uuid
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.document_chunk import DocumentChunk, VectorStatus
from backend.app.repositories.base_repository import BaseRepository


class ChunkRepository(BaseRepository[DocumentChunk]):
    """Repository for DocumentChunk CRUD and batch operations."""

    model = DocumentChunk

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, entity_id: uuid.UUID) -> DocumentChunk | None:
        from sqlalchemy.orm import selectinload
        stmt = (
            select(DocumentChunk)
            .options(selectinload(DocumentChunk.document))
            .where(DocumentChunk.id == entity_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def bulk_create(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """
        Insert multiple chunk records in a single flush.

        Args:
            chunks: List of DocumentChunk instances to insert.

        Returns:
            The list of persisted chunks with generated IDs.
        """
        self._session.add_all(chunks)
        await self._session.flush()
        for chunk in chunks:
            await self._session.refresh(chunk)
        return chunks

    async def get_by_document_id(
        self,
        document_id: uuid.UUID,
    ) -> list[DocumentChunk]:
        """Retrieve all chunks for a document, ordered by index."""
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_paginated_by_document_id(
        self,
        document_id: uuid.UUID,
        offset: int,
        limit: int,
    ) -> list[DocumentChunk]:
        """Retrieve a paginated list of chunks for a document."""
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_document_id(self, document_id: uuid.UUID) -> int:
        """Count the total number of chunks for a document."""
        from sqlalchemy import func
        stmt = select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == document_id)
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    async def update_vector_status(
        self,
        chunk_id: uuid.UUID,
        status: VectorStatus,
        embedding_id: str | None = None,
    ) -> None:
        """Update the vector status (and optionally embedding_id) of a chunk."""
        values: dict = {"vector_status": status}
        if embedding_id is not None:
            values["embedding_id"] = embedding_id

        stmt = (
            update(DocumentChunk)
            .where(DocumentChunk.id == chunk_id)
            .values(**values)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def delete_by_document_id(self, document_id: uuid.UUID) -> None:
        """Delete all chunks belonging to a document (for re-processing)."""
        chunks = await self.get_by_document_id(document_id)
        for chunk in chunks:
            await self._session.delete(chunk)
        await self._session.flush()
