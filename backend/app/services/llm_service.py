"""
LLM Service.

Provider-agnostic interface for invoking language models.
Supports OpenAI, Gemini, Azure, and Ollama via configuration.
"""

import os
import logging
from abc import ABC, abstractmethod

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

LLM_PROVIDER = os.getenv("LLM_PROVIDER") or "openai"
LLM_PROVIDER = LLM_PROVIDER.lower()
LLM_MODEL = os.getenv("LLM_MODEL") or "gpt-4o-mini"

_temp = os.getenv("LLM_TEMPERATURE")
LLM_TEMPERATURE = float(_temp) if _temp else 0.0

_tokens = os.getenv("LLM_MAX_TOKENS")
LLM_MAX_TOKENS = int(_tokens) if _tokens else 1024


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""
    
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a response given a prompt."""
        pass


class OpenAILikeProvider(LLMProvider):
    """
    Provider for OpenAI, Groq, and Ollama.
    They all support the standard OpenAI SDK client.
    """
    def __init__(self):
        # We rely on OPENAI_API_KEY and OPENAI_BASE_URL environment variables
        # being picked up by the AsyncOpenAI client automatically.
        self.client = AsyncOpenAI()
        
    async def generate(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content or ""


class GeminiProvider(LLMProvider):
    """
    Provider for Google Gemini.
    """
    def __init__(self):
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not set.")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(
                model_name=LLM_MODEL,
                generation_config={
                    "temperature": LLM_TEMPERATURE,
                    "max_output_tokens": LLM_MAX_TOKENS,
                }
            )
        except ImportError:
            raise ImportError("google-generativeai package is required for Gemini provider.")
            
    async def generate(self, prompt: str) -> str:
        # Generate async using standard run_in_executor or async SDK if available
        # google-generativeai supports async generate_content_async
        response = await self.model.generate_content_async(prompt)
        return response.text


class AzureOpenAIProvider(LLMProvider):
    """
    Provider for Azure OpenAI.
    """
    def __init__(self):
        from openai import AsyncAzureOpenAI
        self.client = AsyncAzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
    async def generate(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content or ""


class LLMService:
    """
    Main service for interacting with the configured LLM.
    Dispatches to the correct provider.
    """
    def __init__(self):
        self.provider = self._init_provider()
        
    def _init_provider(self) -> LLMProvider:
        if LLM_PROVIDER in ["openai", "ollama", "groq"]:
            return OpenAILikeProvider()
        elif LLM_PROVIDER == "gemini":
            return GeminiProvider()
        elif LLM_PROVIDER == "azure":
            return AzureOpenAIProvider()
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")

    async def answer(self, prompt: str) -> str:
        """Generate a response using the configured provider."""
        logger.info("Generating LLM response using provider: %s", LLM_PROVIDER)
        try:
            return await self.provider.generate(prompt)
        except Exception as e:
            logger.error("LLM Generation failed: %s", e)
            raise
