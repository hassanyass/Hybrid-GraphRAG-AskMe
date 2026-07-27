"""
Document unit tests.

Tests document validation, MinIO storage abstraction, and Postgres metadata
integration by mocking out the actual MinIO client and DB session.
"""

import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from backend.app.models.document import DocumentStatus
from backend.app.services.document_service import DocumentService


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def mock_db_session():
    return AsyncMock()


@pytest.fixture
def mock_storage():
    """Mock StorageService to prevent actual MinIO calls."""
    with patch("backend.app.services.document_service.StorageService") as MockStorage:
        storage_instance = MockStorage.return_value
        storage_instance.upload_file.return_value = "mock_bucket/mock_object_key.pdf"
        yield storage_instance


@pytest.fixture
def mock_repo():
    """Mock DocumentRepository to prevent DB calls."""
    with patch("backend.app.services.document_service.DocumentRepository") as MockRepo:
        repo_instance = MockRepo.return_value
        
        # When create is called, just return the passed document with an ID
        async def mock_create(doc):
            doc.id = uuid.uuid4()
            return doc
            
        repo_instance.create.side_effect = mock_create
        yield repo_instance


# ---------------------------------------------------------------------------
# DocumentService Tests
# ---------------------------------------------------------------------------

class TestDocumentUpload:

    @pytest.mark.asyncio
    async def test_upload_valid_document(self, mock_db_session, mock_storage, mock_repo, user_id):
        """A valid PDF file within size limits should succeed."""
        service = DocumentService(mock_db_session)
        file_stream = io.BytesIO(b"dummy pdf content")
        file_size = len(file_stream.getvalue())

        doc = await service.upload_document(
            user_id=user_id,
            filename="test.pdf",
            content_type="application/pdf",
            file_size=file_size,
            file_stream=file_stream,
        )

        # Verify StorageService was called
        mock_storage.upload_file.assert_called_once()
        
        # Verify Repository was called
        mock_repo.create.assert_called_once()

        # Verify Document properties
        assert doc.user_id == user_id
        assert doc.filename == "test.pdf"
        assert doc.file_type == "application/pdf"
        assert doc.file_size == file_size
        assert doc.status == DocumentStatus.UPLOADED
        assert doc.storage_path == "mock_bucket/mock_object_key.pdf"

    @pytest.mark.asyncio
    async def test_reject_unsupported_file_type(self, mock_db_session, mock_storage, mock_repo, user_id):
        """Uploading an EXE or unsupported type should raise a 400 error."""
        service = DocumentService(mock_db_session)
        file_stream = io.BytesIO(b"executable content")
        
        with pytest.raises(HTTPException) as exc:
            await service.upload_document(
                user_id=user_id,
                filename="test.exe",
                content_type="application/x-msdownload",
                file_size=100,
                file_stream=file_stream,
            )
            
        assert exc.value.status_code == 400
        assert "Unsupported file type" in exc.value.detail
        
        # Should not touch storage or DB
        mock_storage.upload_file.assert_not_called()
        mock_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_reject_oversized_file(self, mock_db_session, mock_storage, mock_repo, user_id):
        """A file exceeding 20MB should be rejected."""
        service = DocumentService(mock_db_session)
        file_stream = io.BytesIO(b"x")
        file_size = 21 * 1024 * 1024  # 21 MB
        
        with pytest.raises(HTTPException) as exc:
            await service.upload_document(
                user_id=user_id,
                filename="large.pdf",
                content_type="application/pdf",
                file_size=file_size,
                file_stream=file_stream,
            )
            
        assert exc.value.status_code == 400
        assert "exceeds maximum allowed size" in exc.value.detail
        mock_storage.upload_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_reject_empty_file(self, mock_db_session, mock_storage, mock_repo, user_id):
        """A file with 0 bytes should be rejected."""
        service = DocumentService(mock_db_session)
        file_stream = io.BytesIO(b"")
        
        with pytest.raises(HTTPException) as exc:
            await service.upload_document(
                user_id=user_id,
                filename="empty.pdf",
                content_type="application/pdf",
                file_size=0,
                file_stream=file_stream,
            )
            
        assert exc.value.status_code == 400
        assert "File is empty" in exc.value.detail


class TestDocumentRetrievalAndDeletion:

    @pytest.mark.asyncio
    async def test_get_document_enforces_user_isolation(self, mock_db_session, mock_storage, mock_repo, user_id):
        """Retrieving a document must enforce that it belongs to the requesting user."""
        service = DocumentService(mock_db_session)
        doc_id = uuid.uuid4()
        
        # Mock repo to return None (simulating not found or belongs to someone else)
        mock_repo.get_document_by_id_and_user = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc:
            await service.get_document(doc_id, user_id)
            
        assert exc.value.status_code == 404
        mock_repo.get_document_by_id_and_user.assert_called_once_with(doc_id, user_id)

    @pytest.mark.asyncio
    async def test_delete_document_success(self, mock_db_session, mock_storage, mock_repo, user_id):
        """Deleting a document should remove it from both storage and DB."""
        service = DocumentService(mock_db_session)
        doc_id = uuid.uuid4()
        
        # Mock repo to return a valid document
        mock_doc = MagicMock()
        mock_doc.storage_path = "mock/path"
        mock_repo.get_document_by_id_and_user = AsyncMock(return_value=mock_doc)
        mock_repo.delete = AsyncMock()
        
        await service.delete_document(doc_id, user_id)
        
        # Verify storage delete was called
        mock_storage.delete_file.assert_called_once_with("mock/path")
        
        # Verify DB delete was called
        mock_repo.delete.assert_called_once_with(mock_doc)
