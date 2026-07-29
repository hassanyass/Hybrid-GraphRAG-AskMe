"""
Response Formatter Service.

Packages the LLM answer, citations, chunks, graph entities, 
and overall confidence into the final structured output.
"""

from dataclasses import dataclass
from typing import Any

from backend.app.models.retrieval import HybridSearchResult, GraphEntity


@dataclass
class Citation:
    """A source citation for the generated answer."""
    filename: str
    page_number: int | None
    section_title: str | None
    chunk_id: str


@dataclass
class QueryResponse:
    """The final structured response returned by the API."""
    answer: str
    sources: list[Citation]
    retrieved_chunks: list[dict[str, Any]]
    graph_entities: list[dict[str, str]]
    confidence: float
    message_id: str | None = None


class ResponseFormatter:
    """Service for formatting the final hybrid query response."""

    def format_response(
        self,
        answer: str,
        retrieved_chunks: list[HybridSearchResult],
        graph_entities: list[GraphEntity]
    ) -> QueryResponse:
        """
        Package all components into a QueryResponse.
        """
        # Extract unique citations
        sources = []
        seen_chunks = set()
        
        for chunk in retrieved_chunks:
            if chunk.chunk_id not in seen_chunks:
                seen_chunks.add(chunk.chunk_id)
                sources.append(
                    Citation(
                        filename=chunk.filename,
                        page_number=chunk.page_number,
                        section_title=chunk.section_title,
                        chunk_id=chunk.chunk_id
                    )
                )

        # Format retrieved chunks for the response payload
        chunks_payload = [
            {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "filename": c.filename,
                "page_number": c.page_number,
                "section_title": c.section_title,
                "score": round(c.score, 4),
                "text": c.chunk_text,
                "preview": c.chunk_text[:200] + "..." if len(c.chunk_text) > 200 else c.chunk_text
            }
            for c in retrieved_chunks
        ]

        # Format graph entities
        entities_payload = [
            {
                "id": e.id,
                "name": e.name,
                "type": e.type
            }
            for e in graph_entities
        ]
        
        # Calculate overall confidence based on the top retrieved chunk
        # If no chunks were retrieved, confidence is 0.0
        confidence = retrieved_chunks[0].score if retrieved_chunks else 0.0

        return QueryResponse(
            answer=answer,
            sources=sources,
            retrieved_chunks=chunks_payload,
            graph_entities=entities_payload,
            confidence=round(confidence, 4)
        )
