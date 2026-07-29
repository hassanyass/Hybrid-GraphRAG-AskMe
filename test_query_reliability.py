"""
Test script for RAG Reliability and Hallucination Prevention.
"""
import asyncio
import sys
import os
import uuid
import logging

sys.path.insert(0, os.getcwd())
from dotenv import load_dotenv
load_dotenv(override=True)

# Set up logging to capture the structured QUERY log
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from backend.app.services.query_engine import QueryEngine
from backend.app.services.hybrid_retriever import HybridRetriever
from backend.app.services.reranker_service import RerankerService
from backend.app.services.context_builder import ContextBuilder
from backend.app.services.prompt_builder import PromptBuilder
from backend.app.services.llm_service import LLMService
from backend.app.services.response_service import ResponseFormatter
from backend.app.database.session import async_session_factory
from backend.app.storage.qdrant_service import QdrantService
from backend.app.storage.neo4j_service import Neo4jService
from backend.app.repositories.chunk_repository import ChunkRepository

async def run_query(question: str):
    async with async_session_factory() as session:
        qdrant = QdrantService()
        neo4j = Neo4jService()
        chunk_repo = ChunkRepository(session)
        
        from backend.app.services.query_service import QueryService
        hybrid_retriever = HybridRetriever(
            qdrant_service=qdrant,
            neo4j_service=neo4j,
            chunk_repo=chunk_repo,
            query_service=QueryService()
        )
        
        engine = QueryEngine(
            hybrid_retriever=hybrid_retriever,
            reranker=RerankerService(chunk_repo=chunk_repo),
            context_builder=ContextBuilder(),
            prompt_builder=PromptBuilder(),
            llm_service=LLMService(),
            response_formatter=ResponseFormatter()
        )
        print(f"\n=======================================================")
        print(f"QUESTION: {question}")
        print(f"=======================================================")
        response = await engine.query(question)
        print(f"\n--- Final Answer ---")
        print(response.answer)
        print(f"\n--- Sources ---")
        for chunk in response.citations:
            print(f"- {chunk.filename} (Page {chunk.page_number})")
        print(f"=======================================================\n")

async def main():
    # Case 1: Question exists in document
    await run_query("What is the Hybrid GraphRAG architecture?")

    # Case 2: Question does not exist
    await run_query("What is the exact recipe for a chocolate cake?")
    
    # Case 3: Totally random string to ensure no vector matches are found
    await run_query("XqY2!zP9#LmK8*vR5")

if __name__ == "__main__":
    asyncio.run(main())
