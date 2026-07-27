"""
DOCX parser.

Extracts text from Microsoft Word documents using python-docx.
"""

import io
import logging

from docx import Document as DocxDocument

from ai_pipeline.parsing.base_parser import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class DocxParser(BaseParser):
    """Extracts text content from DOCX files."""

    def parse(self, file_bytes: bytes) -> ParseResult:
        """
        Extract text from a DOCX file.

        Args:
            file_bytes: Raw DOCX binary data.

        Returns:
            ParseResult with concatenated paragraph text.
        """
        try:
            doc = DocxDocument(io.BytesIO(file_bytes))
            paragraphs: list[str] = []

            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    paragraphs.append(text)

            full_text = "\n\n".join(paragraphs)

            logger.info("Parsed DOCX: %d paragraphs, %d characters", len(paragraphs), len(full_text))
            return ParseResult(text=full_text, page_count=None)

        except Exception as e:
            logger.error("Failed to parse DOCX: %s", e)
            raise ValueError(f"DOCX parsing failed: {e}") from e
