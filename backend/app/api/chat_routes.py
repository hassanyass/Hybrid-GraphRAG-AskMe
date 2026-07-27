"""
Chat API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.schemas import AuthenticatedUser
from backend.app.database.session import get_db_session

from backend.app.services.query_engine import QueryEngine
from backend.app.services.query_service import QueryService
from backend.app.services.hybrid_retriever import HybridRetriever
from backend.app.services.reranker_service import RerankerService
from backend.app.services.context_builder import ContextBuilder
from backend.app.services.prompt_builder import PromptBuilder
from backend.app.services.llm_service import LLMService
from backend.app.services.response_service import ResponseFormatter

from backend.app.storage.qdrant_service import QdrantService
from backend.app.storage.neo4j_service import Neo4jService
from backend.app.repositories.chunk_repository import ChunkRepository


router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


class QueryRequest(BaseModel):
    question: str


def get_query_engine(db: AsyncSession = Depends(get_db_session)) -> QueryEngine:
    """Dependency to build and inject the QueryEngine."""
    chunk_repo = ChunkRepository(db)
    
    qdrant = QdrantService()
    neo4j = Neo4jService()
    
    query_service = QueryService()
    retriever = HybridRetriever(
        query_service=query_service,
        qdrant_service=qdrant,
        neo4j_service=neo4j,
        chunk_repo=chunk_repo
    )
    
    reranker = RerankerService(chunk_repo=chunk_repo)
    context_builder = ContextBuilder()
    prompt_builder = PromptBuilder()
    llm_service = LLMService()
    response_formatter = ResponseFormatter()
    
    return QueryEngine(
        hybrid_retriever=retriever,
        reranker=reranker,
        context_builder=context_builder,
        prompt_builder=prompt_builder,
        llm_service=llm_service,
        response_formatter=response_formatter
    )


@router.post("/query")
async def process_query(
    request: QueryRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    engine: QueryEngine = Depends(get_query_engine),
) -> dict:
    """
    Process a user's question through the hybrid retrieval engine.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Question cannot be empty."
        )
        
    try:
        response = await engine.query(request.question)
        # Convert dataclass to dict using model_dump equivalent or just manually
        # Since it's a dataclass, FastAPI/Pydantic will auto-serialize it if we return it directly,
        # but to match dict output strictly, we let FastAPI handle the dataclass directly.
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Query failed: {e}")
