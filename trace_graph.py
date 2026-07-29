import asyncio
import sys
import os
import uuid
import logging

sys.path.insert(0, os.getcwd())

from backend.app.database.session import async_session_factory
from backend.app.services.graph_extraction_service import GraphExtractionService

logging.basicConfig(level=logging.DEBUG)

async def main():
    doc_id = uuid.UUID("7bb91e7c-cd2c-4ae8-b8ed-442af1e2950f")
    async with async_session_factory() as session:
        graph = GraphExtractionService(session)
        print(f"Tracing GraphExtractionService for doc {doc_id}")
        try:
            await graph.process_chunks(doc_id)
            print("Graph Extraction Successful.")
        except Exception as e:
            print(f"Exception raised in process_chunks: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
