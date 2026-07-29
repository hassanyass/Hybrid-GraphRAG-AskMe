"""
End-to-end graph extraction test.

1. Clears existing Neo4j data.
2. Resets chunk graph_sync_status so they get reprocessed.
3. Runs GraphExtractionService.process_chunks().
4. Queries PostgreSQL, Qdrant, and Neo4j to verify data consistency.
"""
import asyncio
import sys
import os
import uuid
import time

sys.path.insert(0, os.getcwd())
from dotenv import load_dotenv
load_dotenv(override=True)

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

from backend.app.database.session import async_session_factory, engine
from backend.app.services.graph_extraction_service import GraphExtractionService
from backend.app.storage.neo4j_service import Neo4jService
from backend.app.storage.qdrant_service import QdrantService
from sqlalchemy import text

DOC_ID = uuid.UUID("7bb91e7c-cd2c-4ae8-b8ed-442af1e2950f")


async def clear_neo4j():
    """Remove all nodes/relationships so we start fresh."""
    neo = Neo4jService()
    with neo._driver.session() as s:
        s.run("MATCH (n) DETACH DELETE n")
    neo.close()
    print("Neo4j cleared.")


async def reset_chunk_statuses():
    """Reset graph extraction statuses on all chunks so they get reprocessed."""
    async with engine.begin() as conn:
        result = await conn.execute(text(
            f"UPDATE document_chunks "
            f"SET entity_extraction_status = 'PENDING', "
            f"    graph_sync_status = 'PENDING' "
            f"WHERE document_id = '{DOC_ID}'"
        ))
        print(f"Reset graph statuses for {result.rowcount} chunks.")


async def run_extraction():
    """Run the full graph extraction pipeline."""
    print(f"\n{'='*60}")
    print(f"RUNNING GRAPH EXTRACTION FOR DOCUMENT {DOC_ID}")
    print(f"{'='*60}\n")

    start = time.time()
    async with async_session_factory() as session:
        service = GraphExtractionService(session)
        summary = await service.process_chunks(DOC_ID)
        await session.commit()
    elapsed = time.time() - start

    print(f"\n{'='*60}")
    print("EXTRACTION SUMMARY")
    print(f"{'='*60}")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print(f"  elapsed_seconds: {elapsed:.2f}")
    print(f"{'='*60}\n")
    return summary


async def verify_databases():
    """Query all three databases and report counts."""
    print(f"\n{'='*60}")
    print("DATABASE CONSISTENCY VERIFICATION")
    print(f"{'='*60}\n")

    # PostgreSQL
    async with engine.connect() as conn:
        res = await conn.execute(text(
            f"SELECT status FROM documents WHERE id = '{DOC_ID}'"
        ))
        doc_status = res.scalar()

        res = await conn.execute(text(
            f"SELECT COUNT(*) FROM document_chunks WHERE document_id = '{DOC_ID}'"
        ))
        pg_chunks = res.scalar()

    print(f"PostgreSQL:")
    print(f"  Document status: {doc_status}")
    print(f"  Chunk count:     {pg_chunks}")

    # Qdrant
    qdrant = QdrantService()
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    try:
        results = qdrant._client.scroll(
            collection_name=qdrant._collection,
            scroll_filter=Filter(must=[
                FieldCondition(key="document_id", match=MatchValue(value=str(DOC_ID)))
            ]),
            limit=1000,
        )
        qdrant_count = len(results[0])
    except Exception as e:
        qdrant_count = f"ERROR: {e}"

    print(f"\nQdrant:")
    print(f"  Vector count:    {qdrant_count}")

    # Neo4j
    neo = Neo4jService()
    with neo._driver.session() as s:
        doc_nodes = s.run(
            "MATCH (d:Document {id: $doc_id}) RETURN count(d) as cnt",
            doc_id=str(DOC_ID)
        ).single()["cnt"]

        chunk_nodes = s.run(
            "MATCH (d:Document {id: $doc_id})-[:HAS_CHUNK]->(c:Chunk) RETURN count(c) as cnt",
            doc_id=str(DOC_ID)
        ).single()["cnt"]

        entity_nodes = s.run(
            "MATCH (e:Entity) RETURN count(e) as cnt"
        ).single()["cnt"]

        relationships = s.run(
            "MATCH ()-[r]->() RETURN count(r) as cnt"
        ).single()["cnt"]
    neo.close()

    print(f"\nNeo4j:")
    print(f"  Document nodes:  {doc_nodes}")
    print(f"  Chunk nodes:     {chunk_nodes}")
    print(f"  Entity nodes:    {entity_nodes}")
    print(f"  Relationships:   {relationships}")

    print(f"\n{'='*60}")
    print("VERIFICATION COMPLETE")
    print(f"{'='*60}")


async def main():
    await clear_neo4j()
    await reset_chunk_statuses()
    await run_extraction()
    await verify_databases()


if __name__ == "__main__":
    asyncio.run(main())
