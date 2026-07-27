"""
Document API routes.
"""
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.schemas import AuthenticatedUser
from backend.app.database.session import get_db_session
from backend.app.schemas.document_schema import DocumentResponse, DocumentUploadResponse
from backend.app.services.document_service import DocumentService

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentUploadResponse:
    """Upload a new document."""
    if not file.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Filename is required.")
        
    service = DocumentService(db)
    
    # Read to measure size (Spooling in memory/disk by FastAPI)
    file_size = 0
    if file.size is not None:
        file_size = file.size
    else:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
    doc = await service.upload_document(
        user_id=current_user.id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        file_stream=file.file,
    )
    
    return DocumentUploadResponse(
        document_id=doc.id,
        filename=doc.filename,
        status=doc.status,
        created_at=doc.created_at,
    )


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[DocumentResponse]:
    """List documents belonging to the authenticated user."""
    service = DocumentService(db)
    return await service.get_user_documents(current_user.id)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentResponse:
    """Retrieve details of a specific document."""
    service = DocumentService(db)
    return await service.get_document(document_id, current_user.id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a document and its storage."""
    service = DocumentService(db)
    await service.delete_document(document_id, current_user.id)
