"""
Chat API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel
import os
import shutil
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

from backend.app.services.voice_chat_service import VoiceChatService
from backend.app.services.audio_service import AudioService
from backend.app.schemas.voice_schema import VoiceQueryResponse

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


def get_voice_chat_service(engine: QueryEngine = Depends(get_query_engine)) -> VoiceChatService:
    """Dependency to build and inject the VoiceChatService."""
    audio_service = AudioService()
    return VoiceChatService(audio_service=audio_service, query_engine=engine)


@router.post("/voice-query", response_model=VoiceQueryResponse)
async def process_voice_query(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    voice_service: VoiceChatService = Depends(get_voice_chat_service),
) -> VoiceQueryResponse:
    """
    Process a user's voice question through STT, RAG, and TTS.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    temp_file_path = f"/tmp/{file.filename}"
    try:
        os.makedirs("/tmp", exist_ok=True)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        response = await voice_service.process_voice_query(temp_file_path)
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Voice query failed: {e}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
