"""
Hybrid Retriever Service.

Orchestrates vector and graph searches in parallel.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Any

from backend.app.storage.qdrant_service import QdrantService
from backend.app.storage.neo4j_service import Neo4jService
from backend.app.services.query_service import QueryService
from backend.app.models.retrieval import VectorSearchResult, GraphSearchResult
from backend.app.repositories.chunk_repository import ChunkRepository

logger = logging.getLogger(__name__)


@dataclass
class HybridRetrievalOutput:
    """Raw combined output from vector and graph searches."""
    vector_results: list[VectorSearchResult]
    graph_result: GraphSearchResult


class HybridRetriever:
    """Service for running vector and graph searches in parallel."""

    def __init__(
        self,
        query_service: QueryService,
        qdrant_service: QdrantService,
        neo4j_service: Neo4jService,
        chunk_repo: ChunkRepository
    ):
        self._query_service = query_service
        self._qdrant = qdrant_service
        self._neo4j = neo4j_service
        self._chunk_repo = chunk_repo

    async def retrieve(self, query: str, top_k: int = 5, workspace_id: str | None = None) -> HybridRetrievalOutput:
        """
        Run hybrid retrieval for a given user query.
        
        1. Process and embed the query.
        2. Run Qdrant vector search.
        3. Enrich Qdrant results with full chunk text from PostgreSQL.
        4. Trigger lazy graph extraction for any chunks that haven't been extracted yet.
        5. Run Neo4j graph search.
        """
        logger.info("Starting hybrid retrieval for query: '%s'", query)
        
        # 1. Process query
        query_result = await self._query_service.process_query(query)
        
        # 2. Vector search
        loop = asyncio.get_running_loop()
        vector_results = await loop.run_in_executor(
            None, 
            self._qdrant.search, 
            query_result.embedding_vector, 
            top_k,
            workspace_id
        )
        
        # 3. Enrich vector results with database content
        enriched_vectors = []
        pending_chunks = []
        
        for v_res in vector_results:
            try:
                # chunk_id is a string; get_by_id expects uuid.UUID
                chunk_uuid = uuid.UUID(v_res.chunk_id)
                chunk_record = await self._chunk_repo.get_by_id(chunk_uuid)
                if chunk_record:
                    v_res.chunk_text = chunk_record.content
                    v_res.filename = chunk_record.document.filename if chunk_record.document else ""
                    enriched_vectors.append(v_res)
                    
                    # Track chunks that need graph extraction
                    from backend.app.models.document_chunk import GraphExtractionStatus
                    if chunk_record.entity_extraction_status != GraphExtractionStatus.COMPLETED:
                        pending_chunks.append(chunk_record)
                        
            except (ValueError, AttributeError) as e:
                logger.warning("Invalid chunk_id or missing data for chunk %s: %s", v_res.chunk_id, e)
            except Exception as e:
                logger.exception("Failed to enrich chunk %s", v_res.chunk_id)
                
        # 4. Lazy Graph Extraction
        if pending_chunks:
            logger.info("Triggering lazy graph extraction for %d chunks...", len(pending_chunks))
            from backend.app.services.graph_extraction_service import GraphExtractionService
            graph_extractor = GraphExtractionService(self._chunk_repo._session)
            await graph_extractor.process_specific_chunks(pending_chunks)
            
        # 5. Graph search
        graph_result = await loop.run_in_executor(
            None,
            self._neo4j.search_graph,
            query_result.normalized_query,
            workspace_id
        )
                
        return HybridRetrievalOutput(
            vector_results=enriched_vectors,
            graph_result=graph_result
        )
