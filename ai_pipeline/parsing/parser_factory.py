"""
Parser factory.

Maps MIME types to their corresponding parser implementations.
"""

from ai_pipeline.parsing.base_parser import BaseParser
from ai_pipeline.parsing.docx_parser import DocxParser
from ai_pipeline.parsing.pdf_parser import PdfParser
from ai_pipeline.parsing.txt_parser import TxtParser

# Registry of supported MIME types → parser instances
_PARSERS: dict[str, BaseParser] = {
    "application/pdf": PdfParser(),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxParser(),
    "text/plain": TxtParser(),
}


def get_parser(mime_type: str) -> BaseParser:
    """
    Return the appropriate parser for the given MIME type.

    Args:
        mime_type: The MIME type of the document.

    Returns:
        A parser instance.

    Raises:
        ValueError: If the MIME type is not supported.
    """
    parser = _PARSERS.get(mime_type)
    if parser is None:
        supported = ", ".join(_PARSERS.keys())
        raise ValueError(f"Unsupported MIME type: {mime_type}. Supported: {supported}")
    return parser
