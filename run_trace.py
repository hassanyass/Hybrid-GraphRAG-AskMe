import asyncio
import time
import uuid
import sys
import os
import logging

sys.path.insert(0, os.getcwd())

from backend.app.database.session import async_session_factory
from backend.app.services.document_service import DocumentService
from backend.app.services.pipeline_service import PipelineService
from backend.app.services.graph_extraction_service import GraphExtractionService
from backend.app.services.query_engine import QueryEngine
from backend.app.services.reranker_service import RerankerService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trace")

# Intercept logger in reranker_service to catch the warning
reranker_logger = logging.getLogger("backend.app.services.reranker_service")

class RerankerFilter(logging.Filter):
    def filter(self, record):
        if "Failed to fetch graph-connected chunk" in record.getMessage():
            logger.error(f"!!! CAUGHT SWALLOWED EXCEPTION: {record.args[1]} !!!")
        return True

reranker_logger.addFilter(RerankerFilter())

async def main():
    user_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    
    logger.info("--- PHASE 3: Upload Pipeline ---")
    async with async_session_factory() as session:
        doc_service = DocumentService(session)
        pipeline = PipelineService(session)
        
        with open("dummy.pdf", "rb") as f:
            file_bytes = f.read()
            file_size = len(file_bytes)
        
        start = time.perf_counter()
        with open("dummy.pdf", "rb") as f:
            doc = await doc_service.upload_document(user_id, workspace_id, "dummy.pdf", "application/pdf", file_size, f)
        logger.info(f"[Upload Stage] Time: {time.perf_counter()-start:.2f}s | Success | Doc ID: {doc.id}")
        
        original_run_graph = pipeline._run_graph_extraction
        graph_task_future = asyncio.Future()
        
        async def mock_run_graph(doc_id):
            start_g = time.perf_counter()
            await original_run_graph(doc_id)
            logger.info(f"[Neo4j Stage] Graph Sync Time: {time.perf_counter()-start_g:.2f}s | Success")
            graph_task_future.set_result(True)
            
        pipeline._run_graph_extraction = mock_run_graph
        
        start_pipe = time.perf_counter()
        doc = await pipeline.process_document(doc.id, user_id)
        await session.commit()
        
        logger.info(f"[Pipeline Stage] Parse, Chunk, Embed, Qdrant Time: {time.perf_counter()-start_pipe:.2f}s | Success")
        
        await graph_task_future
        
    logger.info("--- PHASE 4 & 5: Retrieval & Knowledge Graph Failure ---")
    async with async_session_factory() as session:
        engine = QueryEngine(session)
        
        original_rerank = engine._reranker.rerank
        async def patched_rerank(vector_results, graph_result):
            logger.info(f"[Reranker] Entered rerank()")
            logger.info(f"[Reranker] Graph chunk IDs returned by Neo4j: {graph_result.connected_chunks}")
            try:
                res = await original_rerank(vector_results, graph_result)
                logger.info(f"[Reranker] Exception was swallowed, context discarded!")
                return res
            except Exception as e:
                logger.info(f"[Reranker] Exception thrown: {e}")
                raise
            
        engine._reranker.rerank = patched_rerank
        
        start_q = time.perf_counter()
        response = await engine.query("What is this document about?", str(workspace_id), str(uuid.uuid4()))
        logger.info(f"[Query] Total Execution time: {time.perf_counter()-start_q:.2f}s")
        logger.info(f"[Prompt Construction] LLM received prompt with graph facts? {not not response.answer}")

if __name__ == "__main__":
    asyncio.run(main())
