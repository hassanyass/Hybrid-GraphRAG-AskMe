"""
Pipeline service.

Orchestrates the complete document processing flow:
  1. Fetch document from PostgreSQL
  2. Download raw file from MinIO
  3. Parse file → raw text
  4. Chunk text → list of chunks
  5. Generate embeddings for all chunks
  6. Persist DocumentChunk records to PostgreSQL
  7. Update DocumentMetadata (page_count, chunk_count)
  8. Update document status (PROCESSING → COMPLETED / FAILED)
"""

import io
import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ai_pipeline.chunking.recursive_chunker import RecursiveChunker
from ai_pipeline.embeddings.embedding_service import EmbeddingService
from ai_pipeline.parsing.parser_factory import get_parser

from backend.app.models.document import Document, DocumentMetadata, DocumentStatus
from backend.app.models.document_chunk import DocumentChunk, VectorStatus
from backend.app.repositories.chunk_repository import ChunkRepository
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.storage.storage_service import StorageService

logger = logging.getLogger(__name__)


class PipelineService:
    """Orchestrates the document → chunks → embeddings pipeline."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._doc_repo = DocumentRepository(session)
        self._chunk_repo = ChunkRepository(session)
        self._storage = StorageService()
        self._chunker = RecursiveChunker()
        self._embedder = EmbeddingService()

    async def process_document(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Document:
        """
        Run the full AI pipeline on an uploaded document.

        Args:
            document_id: The ID of the document to process.
            user_id: The ID of the requesting user (for ownership check).

        Returns:
            The updated Document with status COMPLETED.

        Raises:
            HTTPException: If the document is not found or not processable.
        """
        # 1. Fetch and validate document
        doc = await self._doc_repo.get_document_by_id_and_user(document_id, user_id)
        if not doc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found.")

        if doc.status not in (DocumentStatus.UPLOADED, DocumentStatus.FAILED):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Document is already in {doc.status.value} state.",
            )

        # 2. Mark as PROCESSING
        await self._doc_repo.update_status(document_id, DocumentStatus.PROCESSING)
        logger.info("Pipeline started for document %s (%s)", document_id, doc.filename)

        try:
            # 3. Download raw file from MinIO
            file_bytes = self._download_file(doc.storage_path)
            logger.info("Downloaded %d bytes from MinIO for document %s", len(file_bytes), document_id)

            # 4. Parse file → raw text
            parser = get_parser(doc.file_type)
            parse_result = parser.parse(file_bytes)
            logger.info("Parsed document %s: %d characters extracted", document_id, len(parse_result.text))

            if not parse_result.text.strip():
                raise ValueError("No text content could be extracted from the document.")

            # 5. Chunk text
            chunk_results = self._chunker.chunk(parse_result.text)
            logger.info("Document %s split into %d chunks", document_id, len(chunk_results))

            if not chunk_results:
                raise ValueError("Chunking produced zero chunks.")

            # 6. Generate embeddings
            chunk_texts = [c.content for c in chunk_results]
            embedding_result = self._embedder.embed(chunk_texts)
            logger.info(
                "Generated %d embeddings (model=%s, dim=%d)",
                len(embedding_result.embeddings),
                embedding_result.model_name,
                embedding_result.dimension,
            )

            # 7. Delete any existing chunks (for re-processing support)
            await self._chunk_repo.delete_by_document_id(document_id)

            # 8. Persist chunks to PostgreSQL
            db_chunks: list[DocumentChunk] = []
            for chunk_result in chunk_results:
                db_chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=chunk_result.chunk_index,
                    content=chunk_result.content,
                    token_count=chunk_result.token_count,
                    vector_status=VectorStatus.EMBEDDED,
                    embedding_model=embedding_result.model_name,
                    # embedding_id stays NULL until Phase 6 (Qdrant indexing)
                )
                db_chunks.append(db_chunk)

            await self._chunk_repo.bulk_create(db_chunks)
            logger.info("Persisted %d chunks to PostgreSQL for document %s", len(db_chunks), document_id)

            # 9. Update document metadata
            await self._update_metadata(
                doc=doc,
                page_count=parse_result.page_count,
                chunk_count=len(db_chunks),
            )

            # 10. Mark as COMPLETED
            updated_doc = await self._doc_repo.update_status(document_id, DocumentStatus.COMPLETED)
            logger.info("Pipeline completed for document %s", document_id)
            return updated_doc

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Pipeline failed for document %s: %s", document_id, e)
            await self._doc_repo.update_status(document_id, DocumentStatus.FAILED)
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"Document processing failed: {e}",
            )

    def _download_file(self, storage_path: str) -> bytes:
        """Download a file from MinIO and return its bytes."""
        from backend.app.storage.storage_service import MINIO_BUCKET_NAME

        response = self._storage._client.get_object(
            MINIO_BUCKET_NAME,
            storage_path,
        )
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    async def _update_metadata(
        self,
        doc: Document,
        page_count: int | None,
        chunk_count: int,
    ) -> None:
        """Create or update the document metadata record."""
        if doc.metadata_record:
            doc.metadata_record.page_count = page_count
            doc.metadata_record.chunk_count = chunk_count
        else:
            metadata = DocumentMetadata(
                document_id=doc.id,
                page_count=page_count,
                chunk_count=chunk_count,
            )
            await self._doc_repo.create_metadata(metadata)

        await self._session.flush()
