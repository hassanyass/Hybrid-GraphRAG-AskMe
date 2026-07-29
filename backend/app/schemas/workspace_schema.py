"""
Workspace Pydantic schemas.

Defines request/response data contracts for workspace-related API operations.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
    """Schema for creating a new workspace."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Workspace name")
    description: str | None = Field(None, description="Optional workspace description")


class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace."""
    
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None)


class WorkspaceResponse(BaseModel):
    """Schema for returning workspace data."""
    
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
