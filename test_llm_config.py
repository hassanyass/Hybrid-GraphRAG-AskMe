"""Runtime verification of LLM provider configuration after Groq fix."""
import asyncio
import sys
import os

sys.path.insert(0, os.getcwd())
from dotenv import load_dotenv
load_dotenv(override=True)

from backend.app.services.llm_service import (
    LLM_PROVIDER, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    LLMService, resolve_openai_compatible_config,
)

async def main():
    print("=" * 60)
    print("LLM CONFIGURATION RUNTIME VERIFICATION")
    print("=" * 60)

    # 1. Module-level config
    print(f"\nLLM_PROVIDER:    {LLM_PROVIDER}")
    print(f"LLM_MODEL:       {LLM_MODEL}")
    print(f"LLM_TEMPERATURE: {LLM_TEMPERATURE}")
    print(f"LLM_MAX_TOKENS:  {LLM_MAX_TOKENS}")
    print(f"GROQ_API_KEY:    {'SET (' + os.getenv('GROQ_API_KEY','')[:8] + '...)' if os.getenv('GROQ_API_KEY') else 'NOT SET'}")
    print(f"OPENAI_API_KEY:  {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")

    # 2. Credential resolution
    print("\n--- Credential Resolution ---")
    api_key, base_url = resolve_openai_compatible_config(LLM_PROVIDER)
    print(f"Resolved API key starts with: {api_key[:8]}...")
    print(f"Resolved base_url: {base_url}")

    # 3. LLMService instantiation
    print("\n--- LLMService Instantiation ---")
    try:
        service = LLMService()
        provider = service.provider
        print(f"Provider class:  {type(provider).__name__}")
        print(f"Client class:    {type(provider.client).__name__}")
        print(f"Client base_url: {provider.client.base_url}")
        print(f"Client api_key:  {str(provider.client.api_key)[:8]}...")
        print("LLMService initialized successfully.")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        return

    # 4. LlmExtractor instantiation
    print("\n--- LlmExtractor Instantiation ---")
    try:
        from ai_pipeline.extraction.llm_extractor import LlmExtractor
        extractor = LlmExtractor()
        print(f"Extractor model:    {extractor.model_name}")
        print(f"Extractor client:   {type(extractor._client).__name__}")
        print("LlmExtractor initialized successfully.")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
