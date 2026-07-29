import asyncio
import sys
import os
import uuid
import time
import traceback
from dotenv import load_dotenv

sys.path.insert(0, os.getcwd())
load_dotenv()

from backend.app.database.session import async_session_factory
from backend.app.services.graph_extraction_service import GraphExtractionService
from backend.app.services.llm_service import LLMService, LLM_PROVIDER, LLM_MODEL
from backend.app.repositories.document_repository import DocumentRepository

async def test_llm_config():
    print("\n--- LLM CONFIGURATION AT RUNTIME ---")
    print(f"LLM_PROVIDER: {LLM_PROVIDER}")
    print(f"LLM_MODEL: {LLM_MODEL}")
    
    try:
        llm = LLMService()
        provider = llm.provider
        print(f"Instantiated client class: {type(provider).__name__}")
        if hasattr(provider, 'client'):
            client = provider.client
            print(f"Underlying SDK client: {type(client).__name__}")
            if hasattr(client, 'base_url'):
                print(f"base_url: {client.base_url}")
            else:
                print("base_url: Not found on client")
                
            # Check API keys passed to client
            if hasattr(client, 'api_key'):
                print(f"Client api_key value starts with: {str(client.api_key)[:5]}...")
        else:
            print("Underlying SDK client: Not found")
    except Exception as e:
        print(f"Exception during LLMService initialization: {type(e).__name__}: {e}")
    
    print(f"GROQ_API_KEY from os.environ: {bool(os.getenv('GROQ_API_KEY'))}")
    print(f"OPENAI_API_KEY from os.environ: {bool(os.getenv('OPENAI_API_KEY'))}")
    print("------------------------------------\n")

async def test_graph_extraction():
    print("--- TRACING GRAPH EXTRACTION ---")
    doc_id = uuid.UUID("7bb91e7c-cd2c-4ae8-b8ed-442af1e2950f")
    
    async with async_session_factory() as session:
        print("Entered PipelineService._run_graph_extraction()")
        print(f"Arguments: document_id={doc_id}")
        start_time = time.time()
        
        try:
            graph_service = GraphExtractionService(session)
            print("Entered GraphExtractionService.process_chunks()")
            
            doc_repo = DocumentRepository(session)
            print("Checking DocumentRepository capabilities:")
            print(f"dir(DocumentRepository) contains 'get': {'get' in dir(DocumentRepository)}")
            print(f"dir(DocumentRepository) contains 'get_by_id': {'get_by_id' in dir(DocumentRepository)}")
            
            # Execute the exact failing line
            await graph_service.process_chunks(doc_id)
            
            print(f"GraphExtractionService.process_chunks() returned successfully.")
            
        except Exception as e:
            print("\nEXCEPTION CAUGHT DURING TRACE:")
            print(f"Type: {type(e).__name__}")
            print(f"Message: {e}")
            print("Full Traceback:")
            traceback.print_exc(file=sys.stdout)
            print(f"\nExecution stopped at this line due to {type(e).__name__}.")
        finally:
            elapsed = time.time() - start_time
            print(f"Total execution time: {elapsed:.4f} seconds")
            print("--------------------------------\n")

if __name__ == "__main__":
    asyncio.run(test_llm_config())
    asyncio.run(test_graph_extraction())
