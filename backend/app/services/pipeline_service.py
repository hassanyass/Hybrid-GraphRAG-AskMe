"""
Pipeline service.

Orchestrates the complete document processing flow:
  1. Fetch document from PostgreSQL
  2. Download raw file from MinIO
  3. Parse file → raw text
  4. Chunk text → list of chunks
  5. Contextualize and generate embeddings
  6. Persist DocumentChunk records to PostgreSQL
  7. Sync vectors to Qdrant
  8. Trigger knowledge-graph extraction (background)
  9. Update DocumentMetadata (page_count, chunk_count)
  10. Update document status (PROCESSING → COMPLETED / FAILED)
"""

import asyncio
import io
import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ai_pipeline.chunking.chunking_selector import ChunkingSelector
from ai_pipeline.embeddings.embedding_service import EmbeddingService
from ai_pipeline.parsing.parser_factory import get_parser
from backend.app.services.telemetry_service import TelemetryService
import time

from backend.app.models.document import Document, DocumentMetadata, DocumentStatus
from backend.app.models.document_chunk import DocumentChunk, VectorStatus
from backend.app.repositories.chunk_repository import ChunkRepository
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.storage.storage_service import StorageService
from backend.app.storage.qdrant_service import QdrantService

logger = logging.getLogger(__name__)


class PipelineService:
    """Orchestrates the document → chunks → embeddings pipeline."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._doc_repo = DocumentRepository(session)
        self._chunk_repo = ChunkRepository(session)
        self._storage = StorageService()
        self._embedder = EmbeddingService()
        self._qdrant = QdrantService()

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
            loop = asyncio.get_running_loop()
            parse_result = await loop.run_in_executor(None, parser.parse, file_bytes)
            logger.info("Parsed document %s: %d characters extracted", document_id, len(parse_result.text))

            if not parse_result.text.strip():
                raise ValueError("No text content could be extracted from the document.")

            # 5. Chunk text using pages to preserve metadata
            chunker = ChunkingSelector.get_chunker(doc.file_type)
            chunk_start = time.time()
            chunk_results = await loop.run_in_executor(None, chunker.chunk, parse_result.pages)
            TelemetryService.log_chunk_processing(str(document_id), "Chunking", time.time() - chunk_start, "SUCCESS", {"strategy": type(chunker).__name__, "count": len(chunk_results)})
            logger.info("Document %s split into %d chunks using %s strategy", document_id, len(chunk_results), type(chunker).__name__)

            if not chunk_results:
                raise ValueError("Chunking produced zero chunks.")

            # 6. Prepend contextual metadata to text before embedding
            from datetime import datetime, timezone
            
            chunk_texts = []
            for c in chunk_results:
                context = f"Document: {doc.filename}"
                if c.section_title:
                    context += f" | Section: {c.section_title}"
                context += f"\n{c.content}"
                chunk_texts.append(context)

            embed_start = time.time()
            embedding_result = await loop.run_in_executor(None, self._embedder.embed, chunk_texts)
            embed_duration = time.time() - embed_start
            
            TelemetryService.log_chunk_processing(str(document_id), "Embedding", embed_duration, "SUCCESS", {"model": embedding_result.model_name})
            
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
            now = datetime.now(timezone.utc)
            for chunk_result in chunk_results:
                db_chunk = DocumentChunk(
                    id=uuid.uuid4(),  # explicitly generate UUID to use in Qdrant
                    document_id=document_id,
                    chunk_index=chunk_result.chunk_index,
                    content=chunk_result.content,
                    token_count=chunk_result.token_count,
                    page_number=chunk_result.page_number,
                    language=parse_result.language,
                    chunking_strategy=chunk_result.chunking_strategy,
                    section_title=chunk_result.section_title,
                    section_level=chunk_result.section_level,
                    vector_status=VectorStatus.EMBEDDED,
                    embedding_model=embedding_result.model_name,
                    embedding_dimension=embedding_result.dimension,
                    embedding_version="v1.0",  # static versioning for now
                    vector_generated_at=now,
                )
                db_chunks.append(db_chunk)

            # Insert chunks into Postgres before Qdrant so we have consistent state
            await self._chunk_repo.bulk_create(db_chunks)
            logger.info("Persisted %d chunks to PostgreSQL for document %s", len(db_chunks), document_id)

            # 9. Sync to Qdrant (CPU bound/Blocking IO)
            await loop.run_in_executor(None, self._qdrant.ensure_collection, embedding_result.dimension)
            await loop.run_in_executor(None, self._qdrant.upsert_chunks, db_chunks, embedding_result.embeddings)

            # 10. Trigger knowledge-graph extraction (fire-and-forget background task)
            # SKIPPED: Graph extraction is now lazy and will be handled by the Graph Orchestrator 
            # during query time, saving API tokens and preventing rate limits.
            # asyncio.create_task(
            #     self._run_graph_extraction(document_id),
            #     name=f"graph-extraction-{document_id}",
            # )
            logger.info("Graph extraction skipped (Lazy Generation Mode) for document %s", document_id)

            # 11. Update document metadata
            await self._update_metadata(
                doc=doc,
                page_count=parse_result.page_count,
                chunk_count=len(db_chunks),
            )

            # 12. Mark as COMPLETED
            updated_doc = await self._doc_repo.update_status(document_id, DocumentStatus.COMPLETED)
            
            TelemetryService.log_document_upload(
                document_name=doc.filename,
                pages=parse_result.page_count or 0,
                words=len(parse_result.text.split()),
                chunks=len(db_chunks),
                embedding_time=embed_duration,
                graph_extraction_time=0.0, # Async lazy graph extraction
                llm_calls=0,
                prompt_tokens=0,
                completion_tokens=0
            )
            
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

    async def _run_graph_extraction(self, document_id: uuid.UUID) -> None:
        """
        Background task: run entity extraction and Neo4j sync for a document.

        Uses its own database session so it is fully independent of the
        main pipeline transaction.

        On failure, updates the document status to FAILED so the user
        sees an actionable error instead of a silently incomplete graph.
        """
        from backend.app.database.session import async_session_factory
        from backend.app.services.graph_extraction_service import GraphExtractionService

        try:
            async with async_session_factory() as session:
                graph_service = GraphExtractionService(session)
                summary = await graph_service.process_chunks(document_id)
                await session.commit()

            logger.info(
                "Graph extraction completed for document %s | "
                "Processed: %d | Entities: %d | Relationships: %d",
                document_id,
                summary.get("chunks_processed", 0),
                summary.get("total_entities", 0),
                summary.get("total_relationships", 0),
            )

        except Exception:
            logger.exception(
                "Graph extraction failed for document %s. "
                "Updating document status to FAILED.",
                document_id,
            )
            # Update document status in a fresh session so it is not
            # affected by the failed transaction above.
            try:
                async with async_session_factory() as err_session:
                    from backend.app.repositories.document_repository import DocumentRepository
                    err_repo = DocumentRepository(err_session)
                    await err_repo.update_status(document_id, DocumentStatus.FAILED)
                    await err_session.commit()
            except Exception:
                logger.exception(
                    "Additionally failed to update document %s status to FAILED.",
                    document_id,
                )
