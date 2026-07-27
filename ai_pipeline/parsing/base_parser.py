"""
Base parser interface.

All document format parsers must implement this abstract class
to ensure a consistent extraction API.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ParsedPage:
    """Text content extracted from a single page."""
    page_number: int
    text: str


@dataclass
class ParseResult:
    """Result of parsing a document."""

    pages: list[ParsedPage]
    page_count: int | None = None
    language: str | None = None

    @property
    def text(self) -> str:
        """Concatenated text of all pages for backward compatibility."""
        return "\n\n".join(page.text for page in self.pages)


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    def parse(self, file_bytes: bytes) -> ParseResult:
        """
        Extract text content from raw file bytes.

        Args:
            file_bytes: The raw binary content of the file.

        Returns:
            ParseResult containing the extracted text and optional metadata.
        """
        ...
