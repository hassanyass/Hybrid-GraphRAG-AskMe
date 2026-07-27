"""
Document Pydantic schemas.

Defines request/response data contracts for document-related API
operations, including metadata sub-schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.document import DocumentStatus


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class DocumentCreate(BaseModel):
    """Schema for creating a document record after upload."""

    filename: str = Field(..., max_length=500, description="Original filename.")
    file_type: str = Field(..., max_length=50, description="MIME type or extension.")
    storage_path: str = Field(..., description="Object storage path.")


class DocumentStatusUpdate(BaseModel):
    """Schema for updating document processing status."""

    status: DocumentStatus = Field(..., description="New processing status.")


# ---------------------------------------------------------------------------
# Metadata Schemas
# ---------------------------------------------------------------------------

class DocumentMetadataResponse(BaseModel):
    """Schema for returning document metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    title: str | None = None
    language: str | None = None
    page_count: int | None = None
    chunk_count: int | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class DocumentResponse(BaseModel):
    """Schema for returning document data in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    file_type: str
    storage_path: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    metadata_record: DocumentMetadataResponse | None = None
