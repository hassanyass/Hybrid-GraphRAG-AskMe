"""
Schemas for Voice-to-Voice RAG integration.
"""

from pydantic import BaseModel
from typing import Any

class VoiceQueryResponse(BaseModel):
    """Schema for returning the final Voice RAG response."""
    answer: str
    language: str
    audio_base64: str
    retrieved_chunks: list[dict[str, Any]]
    graph_entities: list[dict[str, str]]
    citations: list[dict[str, Any]]
    response_time: float
    models_used: dict[str, str]
    message_id: str | None = None
