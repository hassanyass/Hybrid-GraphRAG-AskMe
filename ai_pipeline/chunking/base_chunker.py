"""
Base chunker interface and shared models.
"""

import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai_pipeline.parsing.base_parser import ParsedPage

logger = logging.getLogger(__name__)

# Configuration from environment
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
MIN_CHUNK_SIZE = int(os.getenv("MIN_CHUNK_SIZE", "100"))
MAX_CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", "2000"))


@dataclass
class ChunkResult:
    """A single chunk produced from a document."""

    chunk_index: int
    content: str
    token_count: int
    page_number: int | None = None
    chunking_strategy: str = "base"
    section_title: str | None = None
    section_level: int | None = None


class BaseChunker(ABC):
    """
    Abstract base class for chunking strategies.
    """

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        self._chunk_size = chunk_size or CHUNK_SIZE
        self._chunk_overlap = chunk_overlap or CHUNK_OVERLAP
        self._min_chunk_size = MIN_CHUNK_SIZE
        self._max_chunk_size = MAX_CHUNK_SIZE

    @abstractmethod
    def chunk(self, pages: list[ParsedPage]) -> list[ChunkResult]:
        """
        Split parsed pages into chunks.

        Args:
            pages: List of ParsedPage objects.

        Returns:
            Ordered list of ChunkResult objects.
        """
        pass

    def validate_chunks(self, chunks: list[ChunkResult]) -> list[ChunkResult]:
        """
        Filter out chunks that are too small and ensure they aren't larger than the hard maximum.
        If a chunk is too large, it might indicate a failure in the chunking strategy,
        but for now we simply log a warning or enforce the maximum bounds.

        Args:
            chunks: List of newly generated chunks.

        Returns:
            Filtered list of chunks meeting validation criteria.
        """
        valid_chunks = []
        for c in chunks:
            if len(c.content) < self._min_chunk_size:
                logger.debug("Discarding chunk %d: length %d < MIN_CHUNK_SIZE %d", c.chunk_index, len(c.content), self._min_chunk_size)
                continue
            
            if len(c.content) > self._max_chunk_size:
                logger.warning("Chunk %d is too large: length %d > MAX_CHUNK_SIZE %d. It will be kept but should be investigated.", c.chunk_index, len(c.content), self._max_chunk_size)
            
            valid_chunks.append(c)
            
        # Re-index valid chunks to ensure continuous indexing
        for idx, c in enumerate(valid_chunks):
            c.chunk_index = idx

        return valid_chunks
