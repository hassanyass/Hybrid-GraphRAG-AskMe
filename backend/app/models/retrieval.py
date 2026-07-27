"""
Retrieval models.

Defines the structured output of vector, graph, and hybrid retrieval operations.
"""

from dataclasses import dataclass, field
from typing import Any
import uuid


@dataclass
class VectorSearchResult:
    """Result from a vector similarity search."""
    chunk_id: str
    score: float
    document_id: str
    chunk_text: str = ""
    page_number: int | None = None
    section_title: str | None = None
    chunk_index: int = 0
    filename: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEntity:
    """An entity retrieved from the knowledge graph."""
    id: str
    name: str
    type: str


@dataclass
class GraphRelationship:
    """A relationship retrieved from the knowledge graph."""
    source_id: str
    target_id: str
    type: str
    description: str = ""


@dataclass
class GraphSearchResult:
    """Result from a graph search."""
    entities: list[GraphEntity] = field(default_factory=list)
    relationships: list[GraphRelationship] = field(default_factory=list)
    connected_chunks: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class HybridSearchResult:
    """Combined and reranked result from hybrid search."""
    chunk_id: str
    document_id: str
    chunk_text: str
    score: float
    vector_score: float = 0.0
    graph_score: float = 0.0
    page_number: int | None = None
    section_title: str | None = None
    chunk_index: int = 0
    filename: str = ""
