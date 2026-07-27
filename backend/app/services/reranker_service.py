"""
Reranker Service.

Merges results from vector and graph retrieval, deduplicates chunks,
and applies a weighted scoring algorithm.
"""

import os
import logging
from typing import Any

from backend.app.models.retrieval import (
    HybridSearchResult, 
    VectorSearchResult, 
    GraphSearchResult
)
from backend.app.repositories.chunk_repository import ChunkRepository

logger = logging.getLogger(__name__)

_vweight = os.getenv("VECTOR_WEIGHT")
VECTOR_WEIGHT = float(_vweight) if _vweight else 0.7

_gweight = os.getenv("GRAPH_WEIGHT")
GRAPH_WEIGHT = float(_gweight) if _gweight else 0.3


class RerankerService:
    """Service for merging and scoring hybrid retrieval results."""

    def __init__(self, chunk_repo: ChunkRepository):
        self._chunk_repo = chunk_repo

    async def rerank(
        self, 
        vector_results: list[VectorSearchResult], 
        graph_result: GraphSearchResult
    ) -> list[HybridSearchResult]:
        """
        Merge vector and graph chunks, deduplicate, and score.
        """
        chunk_map: dict[str, HybridSearchResult] = {}

        # 1. Process Vector Results
        for v_res in vector_results:
            chunk_map[v_res.chunk_id] = HybridSearchResult(
                chunk_id=v_res.chunk_id,
                document_id=v_res.document_id,
                chunk_text=v_res.chunk_text,
                vector_score=v_res.score,
                graph_score=0.0,
                score=0.0,
                page_number=v_res.page_number,
                section_title=v_res.section_title,
                chunk_index=v_res.chunk_index,
                filename=v_res.filename
            )

        # 2. Process Graph Results
        # Graph returns connected_chunks. We need to fetch their text if not already in chunk_map.
        graph_confidence = graph_result.confidence
        
        missing_chunks = [cid for cid in graph_result.connected_chunks if cid not in chunk_map]
        
        if missing_chunks:
            # Note: A real implementation might do a batch fetch, 
            # here we fetch individually for simplicity given small N.
            for cid in missing_chunks:
                try:
                    record = await self._chunk_repo.get(cid)
                    if record:
                        chunk_map[cid] = HybridSearchResult(
                            chunk_id=cid,
                            document_id=str(record.document_id),
                            chunk_text=record.content,
                            vector_score=0.0,
                            graph_score=0.0,
                            score=0.0,
                            page_number=record.page_number,
                            section_title=record.section_title,
                            chunk_index=record.chunk_index,
                            filename=record.document.filename if record.document else ""
                        )
                except Exception as e:
                    logger.warning("Failed to fetch graph-connected chunk %s: %s", cid, e)

        # Apply Graph Score to ALL connected chunks (both newly added and existing from vector)
        for cid in graph_result.connected_chunks:
            if cid in chunk_map:
                chunk_map[cid].graph_score = graph_confidence

        # 3. Calculate Final Weighted Score
        results = list(chunk_map.values())
        for res in results:
            res.score = (res.vector_score * VECTOR_WEIGHT) + (res.graph_score * GRAPH_WEIGHT)

        # 4. Sort descending by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        logger.info("Reranked %d merged chunks.", len(results))
        return results
