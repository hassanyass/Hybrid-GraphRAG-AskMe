"""
Message model.

Stores individual chat messages within a conversation.
Each message has a role (USER or ASSISTANT) and text content.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import String

from backend.app.database.base import Base


class MessageRole(str, enum.Enum):
    """Identifies the author of a chat message."""

    USER = "USER"
    ASSISTANT = "ASSISTANT"


class Message(Base):
    """Individual chat message within a conversation."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique message identifier.",
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent conversation reference.",
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, name="message_role", create_constraint=True),
        nullable=False,
        comment="Message author role (USER or ASSISTANT).",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Message text content.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp of message creation.",
    )
    audio_storage_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="MinIO object key for generated TTS audio."
    )
    audio_language: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Language of the currently cached audio."
    )
    audio_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when audio was generated."
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role.value}>"
