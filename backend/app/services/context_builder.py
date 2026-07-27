"""
Context Builder Service.

Groups, sorts, and formats retrieved chunks into a final context string
for LLM consumption.
"""

import os
from collections import defaultdict

from backend.app.models.retrieval import HybridSearchResult

_tokens = os.getenv("MAX_CONTEXT_TOKENS")
MAX_CONTEXT_TOKENS = int(_tokens) if _tokens else 4000
# Rough estimation: 1 token ~= 4 chars
MAX_CONTEXT_CHARS = MAX_CONTEXT_TOKENS * 4


class ContextBuilder:
    """Service for building LLM context from retrieval results."""

    def build_context(self, results: list[HybridSearchResult]) -> str:
        """
        Group by document, sort by chunk index, and format.
        Limits the total context size to prevent exceeding token limits.
        """
        if not results:
            return "No relevant context found."

        # Group by document
        doc_groups: dict[str, list[HybridSearchResult]] = defaultdict(list)
        for res in results:
            doc_groups[res.document_id].append(res)
            
        context_parts = []
        current_chars = 0
        
        # Sort documents by highest scoring chunk inside them (so most relevant doc comes first)
        # Sort chunks inside each document by chunk_index to preserve flow
        sorted_docs = sorted(
            doc_groups.items(), 
            key=lambda item: max(c.score for c in item[1]), 
            reverse=True
        )
        
        for doc_id, chunks in sorted_docs:
            chunks.sort(key=lambda c: c.chunk_index)
            
            doc_filename = chunks[0].filename or "Unknown Document"
            doc_header = f"--- Document: {doc_filename} ---"
            
            # Check length early
            if current_chars + len(doc_header) > MAX_CONTEXT_CHARS:
                break
                
            context_parts.append(doc_header)
            current_chars += len(doc_header) + 1
            
            for chunk in chunks:
                chunk_header_parts = [f"Order: {chunk.chunk_index}"]
                if chunk.page_number is not None:
                    chunk_header_parts.append(f"Page: {chunk.page_number}")
                if chunk.section_title:
                    chunk_header_parts.append(f"Section: {chunk.section_title}")
                    
                header = "[" + " | ".join(chunk_header_parts) + "]"
                chunk_text = f"{header}\n{chunk.chunk_text}\n"
                
                if current_chars + len(chunk_text) > MAX_CONTEXT_CHARS:
                    context_parts.append("\n[Context truncated due to size limits...]")
                    return "\n".join(context_parts)
                    
                context_parts.append(chunk_text)
                current_chars += len(chunk_text) + 1
                
        return "\n".join(context_parts)
