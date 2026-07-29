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
from backend.app.services.pipeline_service import PipelineService
from backend.app.storage.storage_service import StorageService

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, BackgroundTasks

async def _run_pipeline_background(document_id: uuid.UUID, user_id: uuid.UUID) -> None:
    from backend.app.database.session import async_session_factory
    from backend.app.services.pipeline_service import PipelineService
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        async with async_session_factory() as session:
            pipeline = PipelineService(session)
            await pipeline.process_document(document_id, user_id)
            await session.commit()
    except Exception as e:
        logger.error(f"Background pipeline failed for document {document_id}: {e}")

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    workspace_id: uuid.UUID = Form(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentUploadResponse:
    """Upload a new document and start background processing."""
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
        workspace_id=workspace_id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        file_stream=file.file,
    )
    
    # Schedule the background processing pipeline
    from backend.app.services.task_queue_manager import TaskQueueManager
    TaskQueueManager.enqueue_background_task(background_tasks, _run_pipeline_background, doc.id, current_user.id)
    
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
    doc = await service.get_document(document_id, current_user.id)
    
    # Map metadata fields to response
    response_data = {
        "id": doc.id,
        "workspace_id": doc.workspace_id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "status": doc.status,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
    }
    
    if doc.metadata_record:
        response_data["chunk_count"] = doc.metadata_record.chunk_count
        response_data["page_count"] = doc.metadata_record.page_count
        
    return DocumentResponse(**response_data)


@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get a presigned URL to download/view the document."""
    service = DocumentService(db)
    doc = await service.get_document(document_id, current_user.id)
    
    if not doc.storage_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document file not found.")
        
    storage = StorageService()
    url = storage.get_file_url(doc.storage_path)
    
    return {"url": url}

from backend.app.schemas.document_schema import PaginatedChunksResponse

@router.get("/{document_id}/chunks", response_model=PaginatedChunksResponse)
async def get_document_chunks(
    document_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> PaginatedChunksResponse:
    """Retrieve a paginated list of chunks for a document."""
    service = DocumentService(db)
    total_chunks, chunks = await service.get_document_chunks_paginated(
        document_id, current_user.id, page, limit
    )
    
    return PaginatedChunksResponse(
        page=page,
        limit=limit,
        total_chunks=total_chunks,
        chunks=[
            {
                "id": c.id,
                "chunk_index": c.chunk_index,
                "content": c.content,
                "token_count": c.token_count,
                "page_number": c.page_number,
                "section_title": c.section_title,
                "vector_status": c.vector_status.value if c.vector_status else "PENDING",
            }
            for c in chunks
        ]
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a document and its storage."""
    service = DocumentService(db)
    await service.delete_document(document_id, current_user.id)


@router.post("/{document_id}/process", status_code=status.HTTP_202_ACCEPTED)
async def process_document(
    document_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Trigger the AI pipeline for an uploaded document in the background.

    Parses the document, splits into chunks, generates embeddings,
    and persists results to PostgreSQL.
    """
    from backend.app.services.task_queue_manager import TaskQueueManager
    TaskQueueManager.enqueue_fire_and_forget(_run_pipeline_background, document_id, current_user.id, task_name=f"process_doc_{document_id}")
    
    return {
        "document_id": str(document_id),
        "status": "PROCESSING",
        "message": "Document processing started in the background.",
    }
