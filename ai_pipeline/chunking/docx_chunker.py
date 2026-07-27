"""
DOCX chunker implementation.
"""

import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

from ai_pipeline.parsing.base_parser import ParsedPage
from ai_pipeline.chunking.base_chunker import BaseChunker, ChunkResult

logger = logging.getLogger(__name__)


class DocxChunker(BaseChunker):
    """
    Chunking strategy for DOCX documents.
    Detects markdown headings (emitted by DocxParser) to preserve section metadata,
    then recursively splits large sections.
    """

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None) -> None:
        super().__init__(chunk_size, chunk_overlap)

        self._headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
            ("#####", "Header 5"),
            ("######", "Header 6"),
        ]

        self._markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self._headers_to_split_on,
            strip_headers=False,
        )

        self._recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        logger.info(
            "DocxChunker initialized: size=%d, overlap=%d",
            self._chunk_size,
            self._chunk_overlap,
        )

    def chunk(self, pages: list[ParsedPage]) -> list[ChunkResult]:
        if not pages:
            logger.warning("Empty pages provided to DocxChunker.")
            return []

        # DOCX usually parses as a single page for now
        full_text = "\n\n".join(p.text for p in pages if p.text.strip())
        
        if not full_text:
            return []

        # Step 1: Split by markdown headings
        md_docs = self._markdown_splitter.split_text(full_text)

        # Step 2: Split large sections recursively
        raw_chunks = self._recursive_splitter.split_documents(md_docs)

        results: list[ChunkResult] = []
        for index, lc_chunk in enumerate(raw_chunks):
            
            # Determine section title and level from metadata
            # Metadata looks like: {"Header 1": "Introduction", "Header 2": "Background"}
            # We take the deepest header
            section_title = None
            section_level = None
            
            for level_num in range(6, 0, -1):
                header_key = f"Header {level_num}"
                if header_key in lc_chunk.metadata:
                    section_title = lc_chunk.metadata[header_key]
                    section_level = level_num
                    break

            results.append(
                ChunkResult(
                    chunk_index=index,
                    content=lc_chunk.page_content,
                    token_count=len(lc_chunk.page_content),
                    page_number=1,  # Entire DOCX is treated as page 1
                    chunking_strategy="docx_heading_aware",
                    section_title=section_title,
                    section_level=section_level,
                )
            )

        logger.info("DocxChunker produced %d raw chunks from %d characters.", len(results), len(full_text))
        
        return self.validate_chunks(results)
