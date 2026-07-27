"""
TXT parser.

Handles plain text files with encoding detection.
"""

import logging

from ai_pipeline.parsing.base_parser import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class TxtParser(BaseParser):
    """Extracts text content from plain text files."""

    def parse(self, file_bytes: bytes) -> ParseResult:
        """
        Decode plain text bytes.

        Attempts UTF-8 first, falls back to latin-1.

        Args:
            file_bytes: Raw text file binary data.

        Returns:
            ParseResult with decoded text content.
        """
        try:
            try:
                text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = file_bytes.decode("latin-1")
                logger.info("TXT file decoded using latin-1 fallback.")

            text = text.strip()
            logger.info("Parsed TXT: %d characters", len(text))
            return ParseResult(text=text, page_count=None)

        except Exception as e:
            logger.error("Failed to parse TXT: %s", e)
            raise ValueError(f"TXT parsing failed: {e}") from e
