import pytest
import os
from unittest.mock import AsyncMock, MagicMock
from backend.app.services.voice_chat_service import VoiceChatService
from backend.app.services.audio_service import TranscriptionResult
from backend.app.services.response_service import QueryResponse, Citation

@pytest.mark.asyncio
async def test_voice_pipeline_english():
    # 1. Setup Mocks
    mock_audio_service = MagicMock()
    mock_audio_service.transcribe_audio = AsyncMock(return_value=TranscriptionResult(
        text="What is GraphRAG?",
        language="en",
        duration=2.5,
        model="whisper-large-v3"
    ))
    mock_audio_service.synthesize_speech = AsyncMock(return_value=b"fake_audio_bytes_en")
    mock_audio_service.tts_model_en = "canopylabs/orpheus-v1-english"
    mock_audio_service.tts_model_ar = "canopylabs/orpheus-arabic-saudi"
    
    mock_query_engine = MagicMock()
    mock_query_engine.query = AsyncMock(return_value=QueryResponse(
        answer="GraphRAG is...",
        sources=[Citation(filename="doc1.pdf", page_number=1, section_title="Intro", chunk_id="chunk1")],
        retrieved_chunks=[{"chunk_id": "chunk1", "text": "GraphRAG is..."}],
        graph_entities=[{"id": "e1", "name": "GraphRAG", "type": "Concept"}],
        confidence=0.95
    ))

    # 2. Execute
    service = VoiceChatService(audio_service=mock_audio_service, query_engine=mock_query_engine)
    response = await service.process_voice_query("/tmp/fake_audio.m4a")

    # 3. Assertions
    assert response.language == "en"
    assert response.answer == "GraphRAG is..."
    assert response.audio_base64 == "ZmFrZV9hdWRpb19ieXRlc19lbg==" # base64 of b"fake_audio_bytes_en"
    assert len(response.citations) == 1
    assert response.models_used["tts_model"] == "canopylabs/orpheus-v1-english"

@pytest.mark.asyncio
async def test_voice_pipeline_arabic():
    # 1. Setup Mocks
    mock_audio_service = MagicMock()
    mock_audio_service.transcribe_audio = AsyncMock(return_value=TranscriptionResult(
        text="ما هو GraphRAG؟",
        language="ar",
        duration=3.0,
        model="whisper-large-v3"
    ))
    mock_audio_service.synthesize_speech = AsyncMock(return_value=b"fake_audio_bytes_ar")
    mock_audio_service.tts_model_en = "canopylabs/orpheus-v1-english"
    mock_audio_service.tts_model_ar = "canopylabs/orpheus-arabic-saudi"
    
    mock_query_engine = MagicMock()
    mock_query_engine.query = AsyncMock(return_value=QueryResponse(
        answer="GraphRAG هو...",
        sources=[Citation(filename="doc2.pdf", page_number=2, section_title="مقدمة", chunk_id="chunk2")],
        retrieved_chunks=[{"chunk_id": "chunk2", "text": "GraphRAG هو..."}],
        graph_entities=[],
        confidence=0.88
    ))

    # 2. Execute
    service = VoiceChatService(audio_service=mock_audio_service, query_engine=mock_query_engine)
    response = await service.process_voice_query("/tmp/fake_audio.m4a")

    # 3. Assertions
    assert response.language == "ar"
    assert response.answer == "GraphRAG هو..."
    assert response.audio_base64 == "ZmFrZV9hdWRpb19ieXRlc19hcg==" # base64 of b"fake_audio_bytes_ar"
    assert response.models_used["tts_model"] == "canopylabs/orpheus-arabic-saudi"
