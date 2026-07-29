"""
Conversation and Message Pydantic schemas.

Defines request/response data contracts for conversation and
message-related API operations.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.message import MessageRole


# ---------------------------------------------------------------------------
# Message Schemas
# ---------------------------------------------------------------------------

class MessageCreate(BaseModel):
    """Schema for adding a message to a conversation."""

    role: MessageRole = Field(..., description="Message author role.")
    content: str = Field(..., min_length=1, description="Message text content.")


class MessageResponse(BaseModel):
    """Schema for returning a message in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Conversation Schemas
# ---------------------------------------------------------------------------

class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    
    workspace_id: uuid.UUID = Field(..., description="ID of the workspace this conversation belongs to.")
    title: str = Field(
        default="New Conversation",
        max_length=300,
        description="Conversation title.",
    )


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""

    title: str | None = Field(
        None,
        max_length=300,
        description="Updated conversation title.",
    )


class ConversationResponse(BaseModel):
    """Schema for returning conversation data in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []
