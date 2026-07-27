"""
Document repository.

Data access layer for Document and DocumentMetadata entities.
Encapsulates all document-related database queries.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.document import Document, DocumentMetadata, DocumentStatus
from backend.app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document CRUD and query operations."""

    model = Document

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Document]:
        """Retrieve documents belonging to a specific user."""
        stmt = (
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: DocumentStatus,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Document]:
        """Retrieve documents filtered by processing status."""
        stmt = (
            select(Document)
            .where(Document.status == status)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        document_id: uuid.UUID,
        new_status: DocumentStatus,
    ) -> Document | None:
        """Update a document's processing status by ID."""
        document = await self.get_by_id(document_id)
        if document is None:
            return None
        document.status = new_status
        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def create_metadata(
        self,
        metadata: DocumentMetadata,
    ) -> DocumentMetadata:
        """Create a metadata record for a document."""
        self._session.add(metadata)
        await self._session.flush()
        await self._session.refresh(metadata)
        return metadata
