"""
Text chunker implementation.
"""

import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ai_pipeline.parsing.base_parser import ParsedPage
from ai_pipeline.chunking.base_chunker import BaseChunker, ChunkResult

logger = logging.getLogger(__name__)


class TxtChunker(BaseChunker):
    """
    Chunking strategy for plain text files.
    Uses standard RecursiveCharacterTextSplitter.
    """

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None) -> None:
        super().__init__(chunk_size, chunk_overlap)
        
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        logger.info(
            "TxtChunker initialized: size=%d, overlap=%d",
            self._chunk_size,
            self._chunk_overlap,
        )

    def chunk(self, pages: list[ParsedPage]) -> list[ChunkResult]:
        if not pages:
            logger.warning("Empty pages provided to TxtChunker.")
            return []

        # Txt files typically have 1 page, but we join just in case
        full_text = "\n\n".join(p.text for p in pages if p.text.strip())
        
        if not full_text:
            return []

        raw_chunks = self._splitter.split_text(full_text)

        results: list[ChunkResult] = []
        for index, chunk_text in enumerate(raw_chunks):
            results.append(
                ChunkResult(
                    chunk_index=index,
                    content=chunk_text,
                    token_count=len(chunk_text),
                    page_number=1,  # Treat txt as single page
                    chunking_strategy="txt_recursive",
                    section_title=None,
                    section_level=None,
                )
            )

        logger.info("TxtChunker produced %d raw chunks from %d characters.", len(results), len(full_text))
        
        return self.validate_chunks(results)
