"""
Document Pydantic schemas.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    """Schema for returning document data in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime


class DocumentUploadResponse(BaseModel):
    """Schema returned immediately after successful upload."""

    document_id: uuid.UUID
    filename: str
    status: DocumentStatus
    created_at: datetime
