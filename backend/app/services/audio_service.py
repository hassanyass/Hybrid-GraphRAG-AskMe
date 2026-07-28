import os
from groq import Groq

from dataclasses import dataclass

@dataclass
class TranscriptionResult:
    text: str
    language: str
    duration: float
    model: str

class AudioService:
    def __init__(self):
        # The Groq client automatically uses the GROQ_API_KEY environment variable.
        self.client = Groq()
        self.stt_model = os.getenv("STT_MODEL", "whisper-large-v3")
        self.tts_model_en = os.getenv("TTS_MODEL_EN", "canopylabs/orpheus-v1-english")
        self.tts_model_ar = os.getenv("TTS_MODEL_AR", "canopylabs/orpheus-arabic-saudi")

    async def transcribe_audio(self, file_path: str) -> TranscriptionResult:
        """
        Transcribe an audio file using Groq's STT (Whisper) model.
        """
        with open(file_path, "rb") as file:
            transcription = self.client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model=self.stt_model,
                temperature=0.0,
                response_format="verbose_json",
            )
            
            # The verbose_json format typically returns language and duration metadata
            return TranscriptionResult(
                text=transcription.text,
                language=getattr(transcription, "language", "en"),
                duration=getattr(transcription, "duration", 0.0),
                model=self.stt_model
            )

    async def synthesize_speech(self, text: str, language: str = "en") -> bytes:
        """
        Synthesize speech from text using the specified TTS model.
        Note: If Groq's SDK does not natively expose `.speech`, this will raise an AttributeError.
        We attempt to use the standard OpenAI-compatible interface structure.
        """
        model = self.tts_model_ar if language.lower() == "ar" else self.tts_model_en
        
        # Assuming the Groq python client supports audio.speech (like OpenAI)
        # If not, this might need to be refactored to use a raw requests POST call.
        try:
            response = self.client.audio.speech.create(
                model=model,
                input=text,
                response_format="mp3"
            )
            # OpenAI's SDK uses response.content for the raw bytes.
            return response.content
        except AttributeError:
            # Fallback if the SDK lacks .speech but the API supports it
            import requests
            api_key = os.getenv("GROQ_API_KEY")
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "input": text,
                "response_format": "mp3"
            }
            # Adjust the URL to Groq's actual audio speech endpoint if different
            # Note: Groq might not have an official /v1/audio/speech yet, but this follows OpenAI standards.
            url = "https://api.groq.com/openai/v1/audio/speech"
            res = requests.post(url, headers=headers, json=data)
            res.raise_for_status()
            return res.content
