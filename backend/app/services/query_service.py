"""
Query processing service.

Responsible for normalizing user queries, detecting empty states,
and generating vector embeddings for downstream retrieval.
"""

from dataclasses import dataclass
import logging

from ai_pipeline.embeddings.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class QueryEmbeddingResult:
    """Result of processing a user query."""
    original_query: str
    normalized_query: str
    embedding_vector: list[float]


class QueryService:
    """Service for processing and embedding user queries."""

    def __init__(self, embedding_service: EmbeddingService | None = None):
        self._embedding_service = embedding_service or EmbeddingService()

    def process_query(self, query: str) -> QueryEmbeddingResult:
        """
        Normalize and embed a user query.
        
        Args:
            query: The raw user query.
            
        Returns:
            QueryEmbeddingResult containing the vector for search.
            
        Raises:
            ValueError: If the query is empty after normalization.
        """
        normalized_query = query.strip()
        
        if not normalized_query:
            raise ValueError("Query cannot be empty.")
            
        logger.info("Processing query: '%s'", normalized_query)
        
        # We process a single query, so we pass a list of length 1
        embedding_result = self._embedding_service.embed([normalized_query])
        
        if not embedding_result.embeddings:
            raise RuntimeError("Failed to generate embedding for the query.")
            
        vector = embedding_result.embeddings[0]
        
        return QueryEmbeddingResult(
            original_query=query,
            normalized_query=normalized_query,
            embedding_vector=vector
        )
