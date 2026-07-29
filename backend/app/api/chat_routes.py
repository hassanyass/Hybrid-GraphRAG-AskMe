"""
Chat API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
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
    workspace_id: str
    conversation_id: str
    response_language: str = "en"


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
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Process a user's question through the hybrid retrieval engine.
    """
    from backend.app.models.message import Message, MessageRole
    from backend.app.repositories.conversation_repository import ConversationRepository
    import uuid
    
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Question cannot be empty."
        )
        
    try:
        conv_repo = ConversationRepository(db)
        conv_id = uuid.UUID(request.conversation_id)
        workspace_id = str(request.workspace_id)
        
        # Save user message
        user_msg = Message(
            conversation_id=conv_id,
            role=MessageRole.USER,
            content=request.question
        )
        await conv_repo.add_message(user_msg)
        
        # We need to pass workspace_id and response_language to engine.query
        response = await engine.query(
            request.question, 
            workspace_id=workspace_id, 
            response_language=request.response_language
        )
        
        assistant_msg = Message(
            conversation_id=conv_id,
            role=MessageRole.ASSISTANT,
            content=response.answer
        )
        await conv_repo.add_message(assistant_msg)
        
        response.message_id = str(assistant_msg.id)
        import dataclasses
        return dataclasses.asdict(response)
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
    workspace_id: str = Form(...),
    conversation_id: str = Form(...),
    response_language: str = Form("en"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    voice_service: VoiceChatService = Depends(get_voice_chat_service),
    db: AsyncSession = Depends(get_db_session),
) -> VoiceQueryResponse:
    """
    Process a user's voice question through STT, RAG, and TTS.
    """
    from backend.app.models.message import Message, MessageRole
    from backend.app.repositories.conversation_repository import ConversationRepository
    import uuid

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    temp_file_path = f"/tmp/{file.filename}"
    try:
        os.makedirs("/tmp", exist_ok=True)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        conv_repo = ConversationRepository(db)
        conv_id = uuid.UUID(conversation_id)
            
        response = await voice_service.process_voice_query(
            temp_file_path, 
            workspace_id=workspace_id, 
            response_language=response_language
        )
        
        # Save user message
        user_msg = Message(
            conversation_id=conv_id,
            role=MessageRole.USER,
            content=f"🎤 *Transcription:* {response.transcription}"
        )
        await conv_repo.add_message(user_msg)
        
        # Save assistant message
        assistant_msg = Message(
            conversation_id=conv_id,
            role=MessageRole.ASSISTANT,
            content=response.answer
        )
        await conv_repo.add_message(assistant_msg)

        response.message_id = str(assistant_msg.id)
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Voice query failed: {e}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

class AudioRequest(BaseModel):
    language: str

@router.post("/messages/{message_id}/audio")
async def generate_message_audio(
    message_id: str,
    request: AudioRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from sqlalchemy import select
    from backend.app.models.message import Message
    from backend.app.storage.storage_service import StorageService
    from backend.app.services.audio_service import AudioService
    import uuid
    from datetime import datetime, timezone
    import io

    try:
        msg_uuid = uuid.UUID(message_id)
        stmt = select(Message).where(Message.id == msg_uuid)
        result = await db.execute(stmt)
        message = result.scalar_one_or_none()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
            
        storage_service = StorageService()
        
        # Cache hit
        if message.audio_storage_path and message.audio_language == request.language:
            return {"audio_url": storage_service.get_file_url(message.audio_storage_path)}
            
        # Cache miss - generate new
        audio_service = AudioService()
        audio_bytes = await audio_service.synthesize_speech(message.content, request.language)
        
        # Upload
        uploaded_path = storage_service.upload_file(
            user_id=current_user.id,
            file_stream=io.BytesIO(audio_bytes),
            filename=f"{message_id}_{request.language}.wav",
            content_type="audio/wav",
            file_size=len(audio_bytes)
        )
        
        # Update db
        message.audio_storage_path = uploaded_path
        message.audio_language = request.language
        message.audio_generated_at = datetime.now(timezone.utc)
        await db.commit()
        
        print("[TTS DEBUG] Saved audio path:", message.audio_storage_path)
        
        return {"audio_url": storage_service.get_file_url(message.audio_storage_path)}
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to generate audio for message {message_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")

