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

    async def process_chunks(self, document_id: uuid.UUID) -> None:
        """
        Process all chunks for a document: extract entities and sync to Neo4j.
        """
        try:
            from backend.app.repositories.document_repository import DocumentRepository
            doc_repo = DocumentRepository(self._session)
            document = await doc_repo.get(document_id)
            if not document:
                logger.error("Document %s not found for graph extraction.", document_id)
                return
            
            # Fetch chunks that need processing
            chunks = await self._chunk_repo.get_by_document_id(document_id)
            if not chunks:
                logger.info("No chunks found for document %s", document_id)
                return

            now = datetime.now(timezone.utc)
            extraction_version = self._extractor.model_name

            for chunk in chunks:
                if chunk.graph_sync_status == GraphSyncStatus.COMPLETED:
                    continue

                try:
                    # 1. Update status to EXTRACTING
                    chunk.entity_extraction_status = GraphExtractionStatus.EXTRACTING
                    await self._session.commit()

                    # 2. Extract Entities and Relationships
                    result = self._extractor.extract(chunk.content)
                    
                    # 3. Mark extraction complete, sync pending
                    chunk.entity_extraction_status = GraphExtractionStatus.COMPLETED
                    chunk.graph_sync_status = GraphSyncStatus.SYNCING
                    await self._session.commit()

                    # 4. Sync to Neo4j
                    entities_dicts = [e.model_dump() for e in result.entities]
                    relationships_dicts = [r.model_dump() for r in result.relationships]
                    
                    doc_meta = {"filename": document.filename, "file_type": document.file_type}
                    chunk_meta = {"chunk_index": chunk.chunk_index, "page_number": chunk.page_number}
                    
                    self._neo4j.sync_document_chunk(
                        document_id=str(document_id),
                        chunk_id=str(chunk.id),
                        entities=entities_dicts,
                        relationships=relationships_dicts,
                        document_metadata=doc_meta,
                        chunk_metadata=chunk_meta
                    )

                    # 5. Mark sync complete
                    chunk.graph_sync_status = GraphSyncStatus.COMPLETED
                    chunk.extraction_version = extraction_version
                    chunk.graph_updated_at = now
                    await self._session.commit()

                    logger.info("Successfully processed graph sync for chunk %s", chunk.id)

                except Exception as e:
                    logger.error("Failed to process graph for chunk %s: %s", chunk.id, e, exc_info=True)
                    chunk.entity_extraction_status = GraphExtractionStatus.FAILED
                    chunk.graph_sync_status = GraphSyncStatus.FAILED
                    await self._session.commit()
        finally:
            # Clean up driver connection
            self._neo4j.close()
