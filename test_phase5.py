import asyncio
import sys
import os
import uuid
import logging

sys.path.insert(0, os.getcwd())

from backend.app.database.session import async_session_factory
from backend.app.services.query_engine import QueryEngine
from backend.app.models.retrieval import VectorSearchResult, GraphSearchResult

logging.basicConfig(level=logging.ERROR)

async def test_reranker_runtime():
    async with async_session_factory() as session:
        engine = QueryEngine(session)
        
        # Patch the retriever to avoid hitting real DBs and avoid downloading BGE-M3
        async def mock_retrieve(*args, **kwargs):
            return [VectorSearchResult(chunk_id=str(uuid.uuid4()), document_id=str(uuid.uuid4()), score=0.9)], GraphSearchResult(connected_chunks=[str(uuid.uuid4())])
        engine._retriever.retrieve = mock_retrieve
        
        # Patch llm to avoid actual LLM calls
        async def mock_answer(*args, **kwargs):
            return "Mock response"
        engine._llm.answer = mock_answer

        original_rerank = engine._reranker.rerank
        async def patched_rerank(vector_results, graph_result):
            print("\n--- PHASE 5 RUNTIME PROOF ---")
            print("1. Entered rerank()")
            print(f"2. Graph chunk IDs: {graph_result.connected_chunks}")
            print(f"3. Calling _chunk_repo.get(cid)...")
            
            res = await original_rerank(vector_results, graph_result)
            
            print(f"6. Graph context discarded (returned map has {len(res)} items)")
            return res
        
        engine._reranker.rerank = patched_rerank
        
        reranker_logger = logging.getLogger("backend.app.services.reranker_service")
        class ExceptionCatcher(logging.Filter):
            def filter(self, record):
                if "Failed to fetch graph-connected chunk" in record.getMessage():
                    print(f"4. AttributeError caught: {record.args[1]}")
                    print(f"5. Exception swallowed (logged as warning)")
                return True
        reranker_logger.addFilter(ExceptionCatcher())

        await engine.query("Test?", str(uuid.uuid4()), str(uuid.uuid4()))

if __name__ == "__main__":
    asyncio.run(test_reranker_runtime())
