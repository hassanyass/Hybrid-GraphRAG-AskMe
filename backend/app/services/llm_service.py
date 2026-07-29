"""
LLM Service.

Provider-agnostic interface for invoking language models.
Supports Groq, OpenAI, Gemini, Azure, and Ollama via configuration.
"""

import os
import logging
from abc import ABC, abstractmethod

from openai import AsyncOpenAI

# API key rotation removed

logger = logging.getLogger(__name__)

LLM_PROVIDER = (os.getenv("LLM_PROVIDER") or "groq").lower()
LLM_MODEL = os.getenv("LLM_MODEL") or "openai/gpt-oss-120b"

_temp = os.getenv("LLM_TEMPERATURE")
LLM_TEMPERATURE = float(_temp) if _temp else 0.0

_tokens = os.getenv("LLM_MAX_TOKENS")
LLM_MAX_TOKENS = int(_tokens) if _tokens else 1024

# Provider-specific base URLs
_PROVIDER_BASE_URLS: dict[str, str] = {
    "groq": "https://api.groq.com/openai/v1",
}


def resolve_openai_compatible_config(provider: str) -> tuple[str, str | None]:
    """
    Resolve the API key and base URL for an OpenAI-compatible provider.

    Returns:
        (api_key, base_url)

    Raises:
        ValueError: If required credentials are missing.
    """
    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in .env")
        base_url = _PROVIDER_BASE_URLS["groq"]
        return api_key, base_url

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "LLM_PROVIDER is set to 'openai' but OPENAI_API_KEY is not set. "
                "Please add OPENAI_API_KEY to your .env file."
            )
        return api_key, None  # default OpenAI endpoint

    if provider == "ollama":
        base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
        return "ollama", base_url  # Ollama ignores the key but SDK requires one

    raise ValueError(f"Cannot resolve credentials for provider '{provider}'.")


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
    def __init__(self, api_key: str, base_url: str | None = None):
        self._api_key = api_key
        self.base_url = base_url
        self.provider = LLM_PROVIDER
        self.client = AsyncOpenAI(api_key=self._api_key, base_url=self.base_url)
        logger.info(
            "Initialized OpenAI-compatible provider (base_url=%s)",
            base_url or "https://api.openai.com/v1",
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
        if LLM_PROVIDER in ("openai", "ollama", "groq"):
            api_key, base_url = resolve_openai_compatible_config(LLM_PROVIDER)
            return OpenAILikeProvider(api_key=api_key, base_url=base_url)
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
