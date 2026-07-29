"""
Models package.

Imports all ORM models so that Alembic and the application can
discover them through a single import.
"""

from backend.app.models.conversation import Conversation
from backend.app.models.workspace import Workspace
from backend.app.models.document import Document, DocumentMetadata, DocumentStatus
from backend.app.models.document_chunk import (
    DocumentChunk,
    GraphExtractionStatus,
    GraphSyncStatus,
    VectorStatus,
)
from backend.app.models.message import Message, MessageRole
from backend.app.models.settings import SystemSetting
from backend.app.models.user import User

__all__ = [
    "Conversation",
    "Workspace",
    "Document",
    "DocumentChunk",
    "DocumentMetadata",
    "DocumentStatus",
    "ExtractionStatus",
    "GraphSyncStatus",
    "Message",
    "MessageRole",
    "SystemSetting",
    "User",
    "VectorStatus",
]
