"""
Audio processing routes for STT and TTS.
"""

import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import io

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.schemas import AuthenticatedUser
from backend.app.services.audio_service import AudioService

router = APIRouter(prefix="/api/v1/audio", tags=["Audio"])

class SynthesizeRequest(BaseModel):
    text: str
    language: str = "en"

def get_audio_service() -> AudioService:
    """Dependency to inject the AudioService."""
    return AudioService()

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    audio_service: AudioService = Depends(get_audio_service),
) -> dict:
    """
    Transcribe an uploaded audio file using Groq Whisper.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Save to a temporary file
    temp_file_path = f"/tmp/{file.filename}"
    try:
        # Create tmp directory if it doesn't exist
        os.makedirs("/tmp", exist_ok=True)
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        transcription_text = await audio_service.transcribe_audio(temp_file_path)
        return {"text": transcription_text}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@router.post("/synthesize")
async def synthesize_speech(
    request: SynthesizeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    audio_service: AudioService = Depends(get_audio_service),
):
    """
    Synthesize speech from text using the specified TTS model on Groq.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Text cannot be empty."
        )
        
    try:
        audio_bytes = await audio_service.synthesize_speech(request.text, request.language)
        return StreamingResponse(
            io.BytesIO(audio_bytes), 
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=synthesized_audio.mp3"}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Synthesis failed: {e}")
