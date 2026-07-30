"""
Service for orchestrating graph entity extraction and Neo4j synchronization.
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ai_pipeline.extraction.llm_extractor import LlmExtractor
from backend.app.models.document_chunk import GraphExtractionStatus, GraphSyncStatus
from backend.app.repositories.chunk_repository import ChunkRepository
from backend.app.storage.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)


class GraphExtractionService:
    """Coordinates entity extraction and Neo4j synchronization for chunks."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._chunk_repo = ChunkRepository(session)
        self._extractor = LlmExtractor()
        self._neo4j = Neo4jService()

    async def process_specific_chunks(self, chunks: list) -> None:
        """
        Extract entities and sync to Neo4j for specific chunks dynamically.
        Used for Lazy Extraction during query time.
        """
        if not chunks:
            return

        now = datetime.now(timezone.utc)
        extraction_version = self._extractor.model_name

        logger.info(
            "LAZY GRAPH EXTRACTION START | Processing %d chunks on-the-fly", len(chunks)
        )

        for i, chunk in enumerate(chunks, 1):
            if chunk.graph_sync_status == GraphSyncStatus.COMPLETED:
                continue

            try:
                # 1. Update status to EXTRACTING
                chunk.entity_extraction_status = GraphExtractionStatus.EXTRACTING
                await self._session.commit()

                # 2. Extract Entities and Relationships via LLM
                logger.info("Lazy LLM extraction | Chunk %d/%d (%s)", i, len(chunks), chunk.id)
                result = self._extractor.extract(chunk.content)

                # 3. Sync to Neo4j
                entities_dicts = [e.model_dump() for e in result.entities]
                relationships_dicts = [r.model_dump() for r in result.relationships]

                # If document is loaded via relationship, get its data. Otherwise default.
                doc = getattr(chunk, 'document', None)
                doc_meta = {
                    "filename": doc.filename if doc else "",
                    "file_type": doc.file_type if doc else "",
                    "workspace_id": str(doc.workspace_id) if (doc and doc.workspace_id) else ""
                }
                chunk_meta = {
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "workspace_id": str(doc.workspace_id) if (doc and doc.workspace_id) else ""
                }

                self._neo4j.sync_document_chunk(
                    document_id=str(chunk.document_id),
                    chunk_id=str(chunk.id),
                    entities=entities_dicts,
                    relationships=relationships_dicts,
                    document_metadata=doc_meta,
                    chunk_metadata=chunk_meta
                )

                # 4. Mark sync complete
                chunk.entity_extraction_status = GraphExtractionStatus.COMPLETED
                chunk.graph_sync_status = GraphSyncStatus.COMPLETED
                chunk.extraction_version = extraction_version
                chunk.graph_updated_at = now
                await self._session.commit()
                
            except Exception:
                logger.exception("Failed lazy graph extraction for chunk %s", chunk.id)
                chunk.entity_extraction_status = GraphExtractionStatus.FAILED
                chunk.graph_sync_status = GraphSyncStatus.FAILED
                await self._session.commit()

        # Clean up driver connection
        self._neo4j.close()

    async def process_chunks(self, document_id: uuid.UUID) -> dict:
        """
        Process all chunks for a document: extract entities and sync to Neo4j.

        Returns:
            Summary dict with counts of processed chunks, entities, and relationships.
        """
        summary = {
            "document_id": str(document_id),
            "chunks_total": 0,
            "chunks_processed": 0,
            "chunks_skipped": 0,
            "chunks_failed": 0,
            "total_entities": 0,
            "total_relationships": 0,
        }

        try:
            from backend.app.repositories.document_repository import DocumentRepository
            doc_repo = DocumentRepository(self._session)
            document = await doc_repo.get_by_id(document_id)
            if not document:
                logger.error("Document %s not found for graph extraction.", document_id)
                raise ValueError(f"Document {document_id} not found for graph extraction.")

            # Fetch chunks that need processing
            chunks = await self._chunk_repo.get_by_document_id(document_id)
            if not chunks:
                logger.info("No chunks found for document %s", document_id)
                return summary

            summary["chunks_total"] = len(chunks)
            now = datetime.now(timezone.utc)
            extraction_version = self._extractor.model_name

            logger.info(
                "GRAPH EXTRACTION START | Document ID: %s | Filename: %s | Chunk count: %d",
                document_id, document.filename, len(chunks),
            )

            for i, chunk in enumerate(chunks, 1):
                if chunk.graph_sync_status == GraphSyncStatus.COMPLETED:
                    summary["chunks_skipped"] += 1
                    logger.debug("Chunk %d/%d (%s) already synced, skipping.", i, len(chunks), chunk.id)
                    continue

                try:
                    # 1. Update status to EXTRACTING
                    chunk.entity_extraction_status = GraphExtractionStatus.EXTRACTING
                    await self._session.commit()

                    # 2. Extract Entities and Relationships via LLM
                    logger.info(
                        "LLM extraction started | Chunk %d/%d (%s) | Content length: %d chars",
                        i, len(chunks), chunk.id, len(chunk.content),
                    )
                    result = self._extractor.extract(chunk.content)

                    entity_count = len(result.entities)
                    rel_count = len(result.relationships)
                    logger.info(
                        "LLM extraction completed | Chunk %d/%d | Entities extracted: %d | Relationships extracted: %d",
                        i, len(chunks), entity_count, rel_count,
                    )

                    # 3. Mark extraction complete, sync pending
                    chunk.entity_extraction_status = GraphExtractionStatus.COMPLETED
                    chunk.graph_sync_status = GraphSyncStatus.SYNCING
                    await self._session.commit()

                    # 4. Sync to Neo4j
                    entities_dicts = [e.model_dump() for e in result.entities]
                    relationships_dicts = [r.model_dump() for r in result.relationships]

                    doc_meta = {
                        "filename": document.filename,
                        "file_type": document.file_type,
                        "workspace_id": str(document.workspace_id) if document.workspace_id else ""
                    }
                    chunk_meta = {
                        "chunk_index": chunk.chunk_index,
                        "page_number": chunk.page_number,
                        "workspace_id": str(document.workspace_id) if document.workspace_id else ""
                    }

                    self._neo4j.sync_document_chunk(
                        document_id=str(document_id),
                        chunk_id=str(chunk.id),
                        entities=entities_dicts,
                        relationships=relationships_dicts,
                        document_metadata=doc_meta,
                        chunk_metadata=chunk_meta
                    )

                    logger.info(
                        "Neo4j sync completed | Chunk %d/%d | Nodes created: %d | Relationships created: %d",
                        i, len(chunks), entity_count, rel_count,
                    )

                    # 5. Mark sync complete
                    chunk.graph_sync_status = GraphSyncStatus.COMPLETED
                    chunk.extraction_version = extraction_version
                    chunk.graph_updated_at = now
                    await self._session.commit()

                    summary["chunks_processed"] += 1
                    summary["total_entities"] += entity_count
                    summary["total_relationships"] += rel_count
                    
                    import asyncio
                    await asyncio.sleep(3)

                except Exception:
                    logger.exception("Failed to process graph for chunk %d/%d (%s)", i, len(chunks), chunk.id)
                    chunk.entity_extraction_status = GraphExtractionStatus.FAILED
                    chunk.graph_sync_status = GraphSyncStatus.FAILED
                    await self._session.commit()
                    summary["chunks_failed"] += 1

            logger.info(
                "GRAPH EXTRACTION COMPLETED | Document ID: %s | "
                "Chunks processed: %d | Skipped: %d | Failed: %d | "
                "Total entities: %d | Total relationships: %d",
                document_id,
                summary["chunks_processed"],
                summary["chunks_skipped"],
                summary["chunks_failed"],
                summary["total_entities"],
                summary["total_relationships"],
            )

        finally:
            # Clean up driver connection
            self._neo4j.close()

        return summary
