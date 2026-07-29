import os
import logging
import re
import wave
import io
from groq import Groq

from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionResult:
    text: str
    language: str
    duration: float
    model: str

class AudioService:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in .env")
        self.client = Groq(api_key=api_key)
        self.stt_model = os.getenv("STT_MODEL", "whisper-large-v3")
        self.tts_model_en = os.getenv("TTS_MODEL_EN", "canopylabs/orpheus-v1-english")
        self.tts_model_ar = os.getenv("TTS_MODEL_AR", "canopylabs/orpheus-arabic-saudi")
        
        logger.info("Initialized AudioService")

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
            
            return TranscriptionResult(
                text=transcription.text,
                language=getattr(transcription, "language", "en"),
                duration=getattr(transcription, "duration", 0.0),
                model=self.stt_model
            )

    def _clean_text_for_tts(self, text: str) -> str:
        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        # Remove inline code
        text = re.sub(r'`[^`]*`', '', text)
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        # Remove citations like [CV.pdf, Page 1] or [1]
        text = re.sub(r'\[.*?\]', '', text)
        # Remove markdown bold/italic
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        # Remove bullet points
        text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
        # Clean up extra whitespace and newlines
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s{2,}', ' ', text)
        return text.strip()

    def _chunk_text_by_sentences(self, text: str, max_chars=2500) -> list[str]:
        # Split by punctuation followed by space
        sentences = re.split(r'(?<=[.!?؟])\s+', text)
        chunks = []
        current_chunk = ""
        for s in sentences:
            if len(current_chunk) + len(s) < max_chars:
                current_chunk += s + " "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = s + " "
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        # Force split if any chunk is still too big
        final_chunks = []
        for chunk in chunks:
            while len(chunk) > max_chars:
                final_chunks.append(chunk[:max_chars])
                chunk = chunk[max_chars:]
            if chunk.strip():
                final_chunks.append(chunk.strip())
        return final_chunks

    def _merge_wav_bytes(self, wav_chunks: list[bytes]) -> bytes:
        if not wav_chunks:
            return b""
        if len(wav_chunks) == 1:
            return wav_chunks[0]
            
        out_io = io.BytesIO()
        
        # Read the first chunk to get params
        with wave.open(io.BytesIO(wav_chunks[0]), 'rb') as w1:
            params = w1.getparams()
            
        with wave.open(out_io, 'wb') as w_out:
            w_out.setparams(params)
            for chunk in wav_chunks:
                try:
                    with wave.open(io.BytesIO(chunk), 'rb') as w_in:
                        w_out.writeframes(w_in.readframes(w_in.getnframes()))
                except wave.Error as e:
                    logger.error(f"Error reading WAV chunk for merging: {e}")
                    
        return out_io.getvalue()

    async def _synthesize_chunk(self, chunk: str, model: str, voice: str) -> bytes:
        try:
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                response_format="wav",
                input=chunk
            )
            return response.content
        except AttributeError:
            import requests
            api_key = self.client.api_key
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "voice": voice,
                "input": chunk,
                "response_format": "wav"
            }
            url = "https://api.groq.com/openai/v1/audio/speech"
            res = requests.post(url, headers=headers, json=data)
            res.raise_for_status()
            return res.content

    async def synthesize_speech(self, text: str, language: str = "en") -> bytes:
        """
        Synthesize speech from text using the specified TTS model and voice.
        Includes preprocessing (cleaning, chunking) to respect Groq's token limits,
        and merges the resulting WAV chunks into a single audio file.
        """
        if language.lower() == "ar":
            model = "canopylabs/orpheus-arabic-saudi"
            voice = "abdullah"
        else:
            model = "canopylabs/orpheus-v1-english"
            voice = "autumn"
            
        clean_text = self._clean_text_for_tts(text)
        if not clean_text:
            return b""
            
        chunks = self._chunk_text_by_sentences(clean_text, max_chars=2500)
        
        wav_bytes_list = []
        for chunk in chunks:
            if chunk.strip():
                try:
                    wav_bytes = await self._synthesize_chunk(chunk, model, voice)
                    if wav_bytes:
                        wav_bytes_list.append(wav_bytes)
                except Exception as e:
                    logger.error(f"Failed to synthesize chunk: {e}")
            
        return self._merge_wav_bytes(wav_bytes_list)
