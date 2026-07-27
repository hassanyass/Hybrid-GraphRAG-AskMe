"""
SystemSetting model.

Stores configurable system parameters as key-value pairs.
Used for runtime configuration that can be changed without
redeploying the application.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database.base import Base


class SystemSetting(Base):
    """Key-value system configuration entry."""

    __tablename__ = "system_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique setting identifier.",
    )
    key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Setting key — must be unique.",
    )
    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Setting value (stored as text).",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp of setting creation.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp of last value change.",
    )

    def __repr__(self) -> str:
        return f"<SystemSetting key={self.key!r}>"
