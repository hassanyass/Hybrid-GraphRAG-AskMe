"""
Chunking strategy selector.
"""

import logging

from ai_pipeline.chunking.base_chunker import BaseChunker
from ai_pipeline.chunking.semantic_token_chunker import SemanticTokenChunker
from ai_pipeline.chunking.docx_chunker import DocxChunker
from ai_pipeline.chunking.txt_chunker import TxtChunker

logger = logging.getLogger(__name__)

class ChunkingSelector:
    """
    Selects the appropriate chunking strategy based on the document type.
    """

    @staticmethod
    def get_chunker(file_type: str) -> BaseChunker:
        """
        Factory method to get the correct chunker for a given MIME type.
        """
        file_type = file_type.lower()

        if file_type == "application/pdf":
            logger.info("Selecting SemanticTokenChunker for %s", file_type)
            return SemanticTokenChunker()
        
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            logger.info("Selecting DocxChunker for %s", file_type)
            return DocxChunker()
            
        elif file_type == "text/plain":
            logger.info("Selecting TxtChunker for %s", file_type)
            return TxtChunker()
            
        else:
            logger.warning("Unknown file_type %s, falling back to TxtChunker", file_type)
            return TxtChunker()
