import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.app.services.query_engine import QueryEngine
from backend.app.services.hybrid_retriever import HybridRetriever
from backend.app.services.reranker_service import RerankerService
from backend.app.services.context_builder import ContextBuilder
from backend.app.services.prompt_builder import PromptBuilder
from backend.app.services.response_service import ResponseFormatter
from backend.app.models.retrieval import VectorSearchResult, GraphSearchResult, GraphEntity


@pytest.fixture
def mock_retriever():
    retriever = AsyncMock(spec=HybridRetriever)
    retriever.retrieve.return_value = MagicMock(
        vector_results=[
            VectorSearchResult(chunk_id="v1", score=0.9, document_id="doc1", chunk_text="Vector chunk text", filename="doc1.pdf")
        ],
        graph_result=GraphSearchResult(
            entities=[GraphEntity(id="e1", name="TestEntity", type="PERSON")],
            relationships=[],
            connected_chunks=["g1"],
            confidence=0.8
        )
    )
    return retriever


@pytest.fixture
def mock_reranker():
    reranker = AsyncMock(spec=RerankerService)
    # Simply return a mock HybridSearchResult list
    from backend.app.models.retrieval import HybridSearchResult
    reranker.rerank.return_value = [
        HybridSearchResult(
            chunk_id="v1",
            document_id="doc1",
            chunk_text="Vector chunk text",
            score=0.85,
            vector_score=0.9,
            graph_score=0.8,
            filename="doc1.pdf"
        )
    ]
    return reranker


@pytest.fixture
def mock_llm_service():
    from backend.app.services.llm_service import LLMService
    llm = AsyncMock(spec=LLMService)
    llm.answer.return_value = "This is the generated answer."
    return llm


@pytest.mark.asyncio
async def test_query_engine_pipeline(mock_retriever, mock_reranker, mock_llm_service):
    """Test the full QueryEngine orchestration pipeline."""
    
    context_builder = ContextBuilder()
    prompt_builder = PromptBuilder()
    response_formatter = ResponseFormatter()
    
    engine = QueryEngine(
        hybrid_retriever=mock_retriever,
        reranker=mock_reranker,
        context_builder=context_builder,
        prompt_builder=prompt_builder,
        llm_service=mock_llm_service,
        response_formatter=response_formatter
    )
    
    response = await engine.query("What is the test entity?")
    
    assert response.answer == "This is the generated answer."
    assert response.confidence == 0.85
    assert len(response.sources) == 1
    assert response.sources[0].chunk_id == "v1"
    assert len(response.graph_entities) == 1
    assert response.graph_entities[0]["name"] == "TestEntity"
    
    mock_retriever.retrieve.assert_called_once_with("What is the test entity?")
    mock_reranker.rerank.assert_called_once()
    mock_llm_service.answer.assert_called_once()
