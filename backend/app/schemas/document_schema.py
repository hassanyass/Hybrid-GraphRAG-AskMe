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
    workspace_id: uuid.UUID | None = None
    filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    
    # Metadata fields derived from DB relationships/queries
    chunk_count: int | None = None
    page_count: int | None = None
    vector_status: str | None = None
    entity_extraction_status: str | None = None
    
    created_at: datetime
    updated_at: datetime


class DocumentChunkResponse(BaseModel):
    """Schema for returning document chunk data."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chunk_index: int
    content: str
    token_count: int
    page_number: int | None = None
    section_title: str | None = None
    vector_status: str


class PaginatedChunksResponse(BaseModel):
    """Schema for a paginated list of document chunks."""

    page: int
    limit: int
    total_chunks: int
    chunks: list[DocumentChunkResponse]


class DocumentUploadResponse(BaseModel):
    """Schema returned immediately after successful upload."""

    document_id: uuid.UUID
    filename: str
    status: DocumentStatus
    created_at: datetime
