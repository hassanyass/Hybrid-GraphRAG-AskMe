import asyncio
import sys
import os
import uuid
import logging

sys.path.insert(0, os.getcwd())

from backend.app.database.session import async_session_factory
from backend.app.services.query_engine import QueryEngine
os.environ["OPENAI_API_KEY"] = "dummy"
from backend.app.api.chat_routes import get_query_engine
from backend.app.services.llm_service import LLMService


logging.basicConfig(level=logging.INFO)

async def capture_prompt():
    workspace_id = "08baa184-4e24-4315-8639-3e3f006825c5" # Using the workspace of the completed doc
    
    async with async_session_factory() as session:
        engine = get_query_engine(session)
        
        # Intercept LLM to print prompt and abort
        original_answer = engine._llm.answer
        async def mock_answer(prompt, *args, **kwargs):
            with open("captured_prompt.txt", "w") as f:
                f.write(prompt)
            print("Prompt written to captured_prompt.txt")
            
            # Print chunks and graph facts included
            chunk_count = prompt.count("Document Chunk:")
            graph_facts = prompt.count("Graph Fact:")
            citations = prompt.count("Citation:")
            
            with open("captured_stats.txt", "w") as f:
                f.write(f"Number of Retrieved Chunks in Prompt: {chunk_count}\n")
                f.write(f"Graph Facts in Prompt: {graph_facts}\n")
                f.write(f"Citations included: {citations}\n")
            
            import sys
            sys.exit(0)
            
        engine._llm.answer = mock_answer
        
        # Execute query
        try:
                    await engine.query("What is the Hybrid GraphRAG software architecture?", workspace_id=workspace_id)
        except SystemExit:
            pass

if __name__ == "__main__":
    asyncio.run(capture_prompt())
