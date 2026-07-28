"""
Voice Chat Orchestration Service.

Orchestrates STT -> Query Engine -> TTS pipeline.
"""
import base64
import logging
import time
from typing import Any

from backend.app.services.audio_service import AudioService
from backend.app.services.query_engine import QueryEngine
from backend.app.schemas.voice_schema import VoiceQueryResponse

logger = logging.getLogger(__name__)

class VoiceChatService:
    """Orchestrates the Voice-to-Voice RAG flow."""
    
    def __init__(self, audio_service: AudioService, query_engine: QueryEngine):
        self.audio_service = audio_service
        self.query_engine = query_engine

    async def process_voice_query(self, audio_file_path: str) -> VoiceQueryResponse:
        """
        Process an end-to-end voice query.
        """
        start_time = time.time()
        logger.info("voice request started")
        
        # 1. STT
        transcription_result = await self.audio_service.transcribe_audio(audio_file_path)
        logger.info("STT completed")
        logger.info(f"language detected: {transcription_result.language}")
        
        # 2. RAG Query
        # We assume the prompt builder has been updated to force same-language response
        query_response = await self.query_engine.query(transcription_result.text)
        logger.info("RAG completed")
        
        # 3. TTS
        audio_bytes = await self.audio_service.synthesize_speech(
            text=query_response.answer, 
            language=transcription_result.language
        )
        logger.info("TTS completed")
        
        # 4. Encode audio to Base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # 5. Construct Models Dictionary
        models_used = {
            "stt_model": transcription_result.model,
            "tts_model": self.audio_service.tts_model_ar if transcription_result.language.lower() == "ar" else self.audio_service.tts_model_en,
            "llm_model": "openai/gpt-oss-120b", # Ideally fetched from env or engine, hardcoding for now or fetching from env
            "embedding_model": "BGE-M3" # Placeholder for embedding model if not easily accessible
        }
        
        import os
        models_used["llm_model"] = os.getenv("LLM_MODEL", models_used["llm_model"])
        models_used["embedding_model"] = os.getenv("EMBEDDING_MODEL", models_used["embedding_model"])

        # Convert citations from dataclass to dict
        citations = []
        for src in query_response.sources:
            citations.append({
                "filename": src.filename,
                "page_number": src.page_number,
                "section_title": src.section_title,
                "chunk_id": src.chunk_id
            })

        response_time = round(time.time() - start_time, 2)
        
        response = VoiceQueryResponse(
            answer=query_response.answer,
            language=transcription_result.language,
            audio_base64=audio_base64,
            retrieved_chunks=query_response.retrieved_chunks,
            graph_entities=query_response.graph_entities,
            citations=citations,
            response_time=response_time,
            models_used=models_used
        )
        
        logger.info("response generated")
        return response
