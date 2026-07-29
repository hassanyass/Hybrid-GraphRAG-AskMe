"""
Document service.

Business logic layer for document uploading, retrieval, and deletion.
"""

import os
import uuid
from typing import BinaryIO

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.document import Document, DocumentStatus
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.storage.storage_service import StorageService
import logging

logger = logging.getLogger(__name__)

# Configuration
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


class DocumentService:
    """Orchestrates document operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = DocumentRepository(session)
        self._storage = StorageService()

    async def upload_document(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        filename: str,
        content_type: str,
        file_size: int,
        file_stream: BinaryIO,
    ) -> Document:
        """
        Validate, upload, and record a new document.
        """
        # Validation
        if file_size == 0:
            logger.warning("Upload failed: file size is 0 bytes for user %s", user_id)
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "File is empty.")
        if file_size > MAX_UPLOAD_SIZE_BYTES:
            logger.warning("Upload failed: file size %s exceeds limit %s for user %s", file_size, MAX_UPLOAD_SIZE_MB, user_id)
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"File exceeds maximum allowed size of {MAX_UPLOAD_SIZE_MB}MB.",
            )
        if content_type not in ALLOWED_MIME_TYPES:
            logger.warning("Upload failed: unsupported content type %s for user %s", content_type, user_id)
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Unsupported file type. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}",
            )

        # Upload to MinIO
        storage_path = self._storage.upload_file(
            user_id=user_id,
            file_stream=file_stream,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
        )

        # Create Database Record
        doc = Document(
            user_id=user_id,
            workspace_id=workspace_id,
            filename=filename,
            file_type=content_type,
            file_size=file_size,
            storage_path=storage_path,
            status=DocumentStatus.UPLOADED,
        )
        
        created_doc = await self._repo.create(doc)
        logger.info("Successfully uploaded document %s (ID: %s) for user %s", filename, created_doc.id, user_id)
        return created_doc

    async def get_user_documents(self, user_id: uuid.UUID) -> list[Document]:
        """List documents owned by the user."""
        return await self._repo.get_by_user_id(user_id)

    async def get_document(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> Document:
        """Retrieve a document, ensuring it belongs to the user."""
        doc = await self._repo.get_document_by_id_and_user(document_id, user_id)
        if not doc:
            logger.warning("Document access denied or not found: doc %s, user %s", document_id, user_id)
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found.")
        return doc

    async def get_document_chunks_paginated(
        self, document_id: uuid.UUID, user_id: uuid.UUID, page: int, limit: int
    ) -> tuple[int, list]:
        """Get paginated chunks for a document ensuring ownership."""
        # Ensure user owns the document
        await self.get_document(document_id, user_id)
        
        from backend.app.repositories.chunk_repository import ChunkRepository
        chunk_repo = ChunkRepository(self._repo._session)
        
        total_chunks = await chunk_repo.count_by_document_id(document_id)
        
        offset = (page - 1) * limit
        chunks = await chunk_repo.get_paginated_by_document_id(document_id, offset, limit)
        
        return total_chunks, chunks

    async def delete_document(self, document_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a document from PostgreSQL and MinIO."""
        doc = await self.get_document(document_id, user_id)
        
        # Delete from MinIO
        self._storage.delete_file(doc.storage_path)

        # Delete from DB
        await self._repo.delete(doc)
        logger.info("Successfully deleted document %s for user %s", document_id, user_id)
