import asyncio
import time
import os
import sys

# Ensure backend module can be imported
sys.path.insert(0, os.getcwd())

from backend.app.database.session import engine
from backend.app.storage.neo4j_service import Neo4jService
from backend.app.storage.qdrant_service import QdrantService
from backend.app.storage.storage_service import StorageService

async def trace_startup():
    start = time.perf_counter()
    print(f"{time.perf_counter()-start:.2f}s Uvicorn starts")
    
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        print(f"{time.perf_counter()-start:.2f}s PostgreSQL connected")
    except Exception as e:
        print(f"{time.perf_counter()-start:.2f}s PostgreSQL failed: {e}")

    try:
        neo4j = Neo4jService()
        neo4j._driver.verify_connectivity()
        print(f"{time.perf_counter()-start:.2f}s Neo4j connected")
    except Exception as e:
        print(f"{time.perf_counter()-start:.2f}s Neo4j failed: {e}")

    try:
        qdrant = QdrantService()
        qdrant._client.get_collections()
        print(f"{time.perf_counter()-start:.2f}s Qdrant connected")
    except Exception as e:
        print(f"{time.perf_counter()-start:.2f}s Qdrant failed: {e}")

    try:
        minio = StorageService()
        minio._client.list_buckets()
        print(f"{time.perf_counter()-start:.2f}s MinIO connected")
    except Exception as e:
        print(f"{time.perf_counter()-start:.2f}s MinIO failed: {e}")

    print(f"{time.perf_counter()-start:.2f}s Routes registered")
    print(f"{time.perf_counter()-start:.2f}s Ready")

if __name__ == '__main__':
    asyncio.run(trace_startup())
