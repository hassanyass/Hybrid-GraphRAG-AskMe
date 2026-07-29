import asyncio
import sys
import os

sys.path.insert(0, os.getcwd())

from backend.app.database.session import engine
from sqlalchemy import text
from backend.app.storage.qdrant_service import QdrantService
from backend.app.storage.neo4j_service import Neo4jService

async def main():
    doc_id = "7bb91e7c-cd2c-4ae8-b8ed-442af1e2950f"
    print(f"--- Document Lifecycle & Completeness Verification ---")
    print(f"Document ID: {doc_id}")
    
    # 1. PostgreSQL Chunks
    async with engine.connect() as conn:
        res = await conn.execute(text(f"SELECT COUNT(*) FROM document_chunks WHERE document_id = '{doc_id}'"))
        pg_chunks = res.scalar()
        print(f"PostgreSQL Chunk Count: {pg_chunks}")

    # 2. Qdrant Vectors
    qdrant = QdrantService()
    try:
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        qdrant_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=doc_id)
                )
            ]
        )
        res = qdrant._client.count(collection_name=qdrant._collection_name, count_filter=qdrant_filter)
        qdrant_chunks = res.count
        print(f"Qdrant Vector Count: {qdrant_chunks}")
    except Exception as e:
        print(f"Qdrant Error: {e}")

    # 3. Neo4j Nodes and Relationships
    neo4j = Neo4jService()
    try:
        with neo4j._driver.session() as session:
            res = session.run("MATCH (c:Chunk {document_id: $doc_id}) RETURN count(c) as count", doc_id=doc_id)
            neo4j_chunks = res.single()["count"]
            print(f"Neo4j Chunk Node Count: {neo4j_chunks}")
            
            res = session.run("MATCH (e:Entity)-[:MENTIONED_IN]->(c:Chunk {document_id: $doc_id}) RETURN count(DISTINCT e) as count", doc_id=doc_id)
            neo4j_entities = res.single()["count"]
            print(f"Neo4j Entity Node Count: {neo4j_entities}")
            
            res = session.run("MATCH (s:Entity)-[r]->(t:Entity) WHERE (s)-[:MENTIONED_IN]->(:Chunk {document_id: $doc_id}) RETURN count(r) as count", doc_id=doc_id)
            neo4j_rels = res.single()["count"]
            print(f"Neo4j Relationship Count: {neo4j_rels}")
    except Exception as e:
        print(f"Neo4j Error: {e}")

if __name__ == '__main__':
    asyncio.run(main())
