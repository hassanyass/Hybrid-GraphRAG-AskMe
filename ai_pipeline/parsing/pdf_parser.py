"""
PDF parser.

Extracts text from PDF documents using PyMuPDF (fitz).
Preserves paragraph structure and handles multi-page documents.
"""

import logging

import fitz  # PyMuPDF

from ai_pipeline.parsing.base_parser import BaseParser, ParsedPage, ParseResult

logger = logging.getLogger(__name__)


class PdfParser(BaseParser):
    """Extracts text content from PDF files."""

    def parse(self, file_bytes: bytes) -> ParseResult:
        """
        Extract text from a PDF file.

        Args:
            file_bytes: Raw PDF binary data.

        Returns:
            ParseResult with concatenated page text and page count.
        """
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pages: list[ParsedPage] = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text")
                if text.strip():
                    # 1-indexed page numbers
                    pages.append(ParsedPage(page_number=page_num + 1, text=text.strip()))

            doc.close()

            page_count = len(doc)
            full_text = "\n\n".join(p.text for p in pages)

            logger.info("Parsed PDF: %d pages, %d characters", len(pages), len(full_text))
            return ParseResult(pages=pages, page_count=page_count)

        except Exception as e:
            logger.error("Failed to parse PDF: %s", e)
            raise ValueError(f"PDF parsing failed: {e}") from e
