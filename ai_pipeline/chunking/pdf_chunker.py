"""
PDF chunker implementation.
"""

import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument

from ai_pipeline.parsing.base_parser import ParsedPage
from ai_pipeline.chunking.base_chunker import BaseChunker, ChunkResult

logger = logging.getLogger(__name__)


class PdfChunker(BaseChunker):
    """
    Chunking strategy for PDF documents.
    Uses RecursiveCharacterTextSplitter but maps page numbers cleanly.
    Future phases can implement section detection from PyMuPDF.
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
            "PdfChunker initialized: size=%d, overlap=%d",
            self._chunk_size,
            self._chunk_overlap,
        )

    def chunk(self, pages: list[ParsedPage]) -> list[ChunkResult]:
        if not pages:
            logger.warning("Empty pages provided to PdfChunker.")
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
                    token_count=len(lc_chunk.page_content),
                    page_number=lc_chunk.metadata.get("page_number"),
                    chunking_strategy="pdf_recursive",
                    section_title=None,
                    section_level=None,
                )
            )

        logger.info("PdfChunker produced %d raw chunks from %d pages.", len(results), len(pages))
        
        return self.validate_chunks(results)
