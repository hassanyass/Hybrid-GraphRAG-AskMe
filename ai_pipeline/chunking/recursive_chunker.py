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


from ai_pipeline.parsing.base_parser import ParsedPage
from langchain_core.documents import Document as LangchainDocument


@dataclass
class ChunkResult:
    """A single chunk produced from a document."""

    chunk_index: int
    content: str
    token_count: int
    page_number: int | None = None


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

    def chunk(self, pages: list[ParsedPage]) -> list[ChunkResult]:
        """
        Split text into chunks while preserving metadata.

        Args:
            pages: List of ParsedPage objects containing text and metadata.

        Returns:
            Ordered list of ChunkResult objects.
        """
        if not pages:
            logger.warning("Empty pages provided to chunker.")
            return []

        # Convert ParsedPage to Langchain Document
        lc_docs = [
            LangchainDocument(
                page_content=page.text,
                metadata={"page_number": page.page_number}
            )
            for page in pages
            if page.text.strip()
        ]

        if not lc_docs:
            return []

        raw_chunks = self._splitter.split_documents(lc_docs)

        results: list[ChunkResult] = []
        for index, lc_chunk in enumerate(raw_chunks):
            results.append(
                ChunkResult(
                    chunk_index=index,
                    content=lc_chunk.page_content,
                    token_count=len(lc_chunk.page_content),  # Character-level count
                    page_number=lc_chunk.metadata.get("page_number"),
                )
            )

        logger.info("Produced %d chunks from %d pages.", len(results), len(pages))
        return results
