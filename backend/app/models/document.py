"""
Document and DocumentMetadata models.

Stores uploaded document records and their extracted metadata.
Document status tracks the processing lifecycle from upload
through AI pipeline completion.
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


class DocumentStatus(str, enum.Enum):
    """Processing lifecycle status for a document."""

    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Document(Base):
    """Uploaded document record."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique document identifier.",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user reference.",
    )
    filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Original uploaded filename.",
    )
    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="MIME type or file extension (e.g. 'application/pdf').",
    )
    storage_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Object storage path (MinIO key).",
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status", create_constraint=True),
        default=DocumentStatus.UPLOADED,
        nullable=False,
        index=True,
        comment="Current processing status.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp of document upload.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp of last status change.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    user: Mapped["User"] = relationship(
        "User",
        back_populates="documents",
    )
    metadata_record: Mapped["DocumentMetadata"] = relationship(
        "DocumentMetadata",
        back_populates="document",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.filename!r} status={self.status.value}>"


class DocumentMetadata(Base):
    """Additional metadata extracted from a document after processing."""

    __tablename__ = "document_metadata"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique metadata record identifier.",
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Parent document reference (one-to-one).",
    )
    title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Extracted or user-provided document title.",
    )
    language: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Detected document language (ISO 639-1 code).",
    )
    page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of pages in the document.",
    )
    chunk_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of text chunks produced by the AI pipeline.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp of metadata creation.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="metadata_record",
    )

    def __repr__(self) -> str:
        return f"<DocumentMetadata id={self.id} document_id={self.document_id}>"
