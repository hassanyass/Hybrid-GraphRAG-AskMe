"""
Semantic Token Chunker implementation.

Splits documents into semantically coherent chunks using a token-based limit,
respecting paragraph and sentence boundaries as much as possible.
"""

import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ai_pipeline.parsing.base_parser import ParsedPage
from ai_pipeline.chunking.base_chunker import BaseChunker, ChunkResult

logger = logging.getLogger(__name__)


class SemanticTokenChunker(BaseChunker):
    """
    Chunking strategy that relies on token counts and semantic separators.
    Configured for 400-600 tokens with 50-100 overlap.
    """

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None) -> None:
        # Defaults optimized for BGE-M3 context sizes (typically dense models prefer ~500 tokens)
        super().__init__(chunk_size=chunk_size or 500, chunk_overlap=chunk_overlap or 50)
        
        # We use a custom length function approximation if a specific tokenizer isn't provided.
        # Alternatively, langchain supports from_tiktoken_encoder, but length=len is roughly char-based.
        # To strictly use tokens, we use character heuristics (1 token ~ 4 chars) for speed,
        # or we could use tiktoken if we want exact metrics.
        # Here we approximate: chunk_size tokens * 4 = char size
        approx_char_size = self._chunk_size * 4
        approx_char_overlap = self._chunk_overlap * 4

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=approx_char_size,
            chunk_overlap=approx_char_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        logger.info(
            "SemanticTokenChunker initialized: target_tokens=%d, overlap_tokens=%d (approx chars %d/%d)",
            self._chunk_size,
            self._chunk_overlap,
            approx_char_size,
            approx_char_overlap
        )

    def chunk(self, pages: list[ParsedPage]) -> list[ChunkResult]:
        if not pages:
            logger.warning("Empty pages provided to SemanticTokenChunker.")
            return []

        results: list[ChunkResult] = []
        global_index = 0

        for page in pages:
            if not page.text.strip():
                continue
                
            raw_chunks = self._splitter.split_text(page.text)
            
            for text_chunk in raw_chunks:
                # Approximate token count: chars / 4
                token_count = len(text_chunk) // 4
                
                results.append(
                    ChunkResult(
                        chunk_index=global_index,
                        content=text_chunk,
                        token_count=token_count,
                        page_number=page.page_number,
                        chunking_strategy="semantic_token",
                        section_title=None,
                        section_level=None,
                    )
                )
                global_index += 1

        logger.info("SemanticTokenChunker produced %d chunks from %d pages.", len(results), len(pages))
        
        return self.validate_chunks(results)
