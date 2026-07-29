"""
Tests for QdrantService.
"""

import uuid
import pytest
from unittest.mock import MagicMock, patch

from backend.app.models.document_chunk import DocumentChunk
from backend.app.storage.qdrant_service import QdrantService


@pytest.fixture
def mock_qdrant_client():
    with patch("backend.app.storage.qdrant_service.QdrantClient") as mock_client_class:
        mock_instance = mock_client_class.return_value
        # Mock get_collections to return empty initially
        mock_instance.get_collections.return_value = MagicMock(collections=[])
        yield mock_instance


def test_ensure_collection_creates_when_missing(mock_qdrant_client):
    service = QdrantService()
    service.ensure_collection(dimension=1024)
    
    mock_qdrant_client.create_collection.assert_called_once()
    _, kwargs = mock_qdrant_client.create_collection.call_args
    assert kwargs["collection_name"] == "document_chunks"
    assert kwargs["vectors_config"].size == 1024


def test_ensure_collection_skips_when_exists(mock_qdrant_client):
    mock_collection = MagicMock()
    mock_collection.name = "document_chunks"
    mock_qdrant_client.get_collections.return_value = MagicMock(collections=[mock_collection])
    
    # Mock collection_info to return existing dimension of 1024
    mock_collection_info = MagicMock()
    mock_collection_info.config.params.vectors.size = 1024
    mock_qdrant_client.get_collection.return_value = mock_collection_info
    
    service = QdrantService()
    service.ensure_collection(dimension=1024)
    
    mock_qdrant_client.create_collection.assert_not_called()


def test_upsert_chunks(mock_qdrant_client):
    service = QdrantService()
    
    chunk_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    chunk = DocumentChunk(
        id=chunk_id,
        document_id=doc_id,
        chunk_index=0,
        chunking_strategy="txt",
        content="Test content",
        page_number=1,
    )
    vector = [0.1] * 1024
    
    service.upsert_chunks([chunk], [vector])
    
    mock_qdrant_client.upsert.assert_called_once()
    _, kwargs = mock_qdrant_client.upsert.call_args
    assert kwargs["collection_name"] == "document_chunks"
    points = kwargs["points"]
    assert len(points) == 1
    
    point = points[0]
    assert point.id == str(chunk_id)
    assert point.vector == vector
    assert point.payload["document_id"] == str(doc_id)
    assert point.payload["chunk_index"] == 0
    assert point.payload["chunking_strategy"] == "txt"
    assert point.payload["page_number"] == 1


def test_upsert_chunks_mismatch(mock_qdrant_client):
    service = QdrantService()
    chunk = DocumentChunk(id=uuid.uuid4())
    vector = [0.1]
    
    with pytest.raises(ValueError, match="Mismatch"):
        service.upsert_chunks([chunk, chunk], [vector])
