"""
DocumentChunk model.

Stores individual text chunks produced from uploaded documents.
Each chunk tracks its processing status across the AI pipeline:
  - Vector embedding status (for Qdrant integration)
  - Entity extraction status (for Neo4j knowledge graph)
  - Graph synchronization status (for Neo4j integration)

These status fields are designed to be updated by future pipeline
phases without requiring schema changes.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


# ---------------------------------------------------------------------------
# Enum Types
# ---------------------------------------------------------------------------


class VectorStatus(str, enum.Enum):
    """Tracks the lifecycle of a chunk's vector embedding."""

    PENDING = "PENDING"        # Chunk created, not yet embedded
    EMBEDDED = "EMBEDDED"      # Embedding generated, not yet pushed to Qdrant
    INDEXED = "INDEXED"        # Successfully stored in Qdrant
    FAILED = "FAILED"          # Embedding or indexing failed


class ExtractionStatus(str, enum.Enum):
    """Tracks entity/relationship extraction from a chunk."""

    PENDING = "PENDING"        # Not yet processed
    EXTRACTING = "EXTRACTING"  # Currently being processed by LLM
    COMPLETED = "COMPLETED"    # Extraction finished successfully
    FAILED = "FAILED"          # Extraction failed


class GraphSyncStatus(str, enum.Enum):
    """Tracks synchronization of extracted entities to Neo4j."""

    PENDING = "PENDING"        # Entities not yet pushed to Neo4j
    SYNCED = "SYNCED"          # Successfully stored in Neo4j
    FAILED = "FAILED"          # Sync to Neo4j failed


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


class DocumentChunk(Base):
    """A text chunk extracted from a document for AI processing."""

    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique chunk identifier.",
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent document reference.",
    )

    # ------------------------------------------------------------------
    # Core Chunk Data
    # ------------------------------------------------------------------
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequential position of this chunk within the document.",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The actual text content of the chunk.",
    )
    token_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of tokens in the chunk (model-dependent).",
    )
    page_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="The page number this chunk originated from (1-indexed).",
    )
    language: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Detected language for this specific chunk.",
    )
    chunking_strategy: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="recursive",
        comment="The chunking strategy used to produce this chunk.",
    )
    section_title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Title of the section this chunk belongs to (if detected).",
    )
    section_level: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Heading depth level for the section (e.g., 1 for H1, 2 for H2).",
    )

    # ------------------------------------------------------------------
    # Qdrant Vector Storage Tracking (Phase 6)
    # ------------------------------------------------------------------
    embedding_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Point ID of the vector in Qdrant.",
    )
    vector_status: Mapped[VectorStatus] = mapped_column(
        Enum(VectorStatus, name="vector_status_enum", create_constraint=True),
        default=VectorStatus.PENDING,
        nullable=False,
        index=True,
        comment="Current status of vector embedding for this chunk.",
    )
    embedding_model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Name of the embedding model used (e.g. BGE-M3).",
    )

    # ------------------------------------------------------------------
    # Neo4j Knowledge Graph Tracking (Phase 6)
    # ------------------------------------------------------------------
    entity_extraction_status: Mapped[ExtractionStatus] = mapped_column(
        Enum(ExtractionStatus, name="entity_extraction_status_enum", create_constraint=True),
        default=ExtractionStatus.PENDING,
        nullable=False,
        index=True,
        comment="Status of entity/relationship extraction from this chunk.",
    )
    graph_sync_status: Mapped[GraphSyncStatus] = mapped_column(
        Enum(GraphSyncStatus, name="graph_sync_status_enum", create_constraint=True),
        default=GraphSyncStatus.PENDING,
        nullable=False,
        index=True,
        comment="Status of synchronization to Neo4j knowledge graph.",
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp of chunk creation.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp of last status update.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="chunks",
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentChunk id={self.id} document_id={self.document_id} "
            f"index={self.chunk_index} vector={self.vector_status.value}>"
        )
