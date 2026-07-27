"""
Recursive document chunker.

Splits extracted text into semantically meaningful chunks
with configurable size and overlap using LangChain text splitters.
"""

import os
import logging
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# Configuration from environment
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))


@dataclass
class ChunkResult:
    """A single chunk produced from a document."""

    chunk_index: int
    content: str
    token_count: int


class RecursiveChunker:
    """
    Splits text into overlapping chunks using recursive character splitting.

    The splitter tries to split on paragraphs first, then sentences,
    then words, ensuring chunks stay within the configured size.
    """

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        self._chunk_size = chunk_size or CHUNK_SIZE
        self._chunk_overlap = chunk_overlap or CHUNK_OVERLAP

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        logger.info(
            "Chunker initialized: size=%d, overlap=%d",
            self._chunk_size,
            self._chunk_overlap,
        )

    def chunk(self, text: str) -> list[ChunkResult]:
        """
        Split text into chunks.

        Args:
            text: The full document text to split.

        Returns:
            Ordered list of ChunkResult objects.
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to chunker.")
            return []

        raw_chunks = self._splitter.split_text(text)

        results: list[ChunkResult] = []
        for index, chunk_text in enumerate(raw_chunks):
            results.append(
                ChunkResult(
                    chunk_index=index,
                    content=chunk_text,
                    token_count=len(chunk_text),  # Character-level count; refined in future phases
                )
            )

        logger.info("Produced %d chunks from %d characters of text.", len(results), len(text))
        return results
