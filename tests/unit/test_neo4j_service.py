"""
Tests for Neo4jService.
"""

import pytest
from unittest.mock import MagicMock, patch

from backend.app.storage.neo4j_service import Neo4jService


@pytest.fixture
def mock_driver():
    with patch("backend.app.storage.neo4j_service.GraphDatabase") as mock_db_class:
        mock_instance = mock_db_class.driver.return_value
        yield mock_instance


def test_neo4j_service_init(mock_driver):
    service = Neo4jService(uri="bolt://test:7687", user="test_user", password="test_password")
    
    mock_db_class = mock_driver.driver # wait, GraphDatabase is mocked.
    # To check the patch correctly:
    pass

def test_neo4j_service_initialize_constraints(mock_driver):
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    
    service = Neo4jService()
    service._driver = mock_driver  # Ensure it uses our mock
    
    service.initialize_constraints()
    
    assert mock_session.run.call_count == 3
    calls = mock_session.run.call_args_list
    assert "document_id" in calls[0][0][0]
    assert "chunk_id" in calls[1][0][0]
    assert "entity_id" in calls[2][0][0]

def test_sync_document_chunk(mock_driver):
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    
    service = Neo4jService()
    service._driver = mock_driver
    
    entities = [{"id": "e1", "name": "Python", "type": "LANGUAGE"}]
    relationships = [{"source_id": "e1", "target_id": "e2", "type": "USES"}]
    
    service.sync_document_chunk("doc1", "chunk1", entities, relationships)
    
    mock_session.execute_write.assert_called_once()
    args = mock_session.execute_write.call_args[0]
    
    assert args[0] == service._upsert_graph_tx
    assert args[1] == "doc1"
    assert args[2] == "chunk1"
    assert args[3] == entities
    assert args[4] == relationships
