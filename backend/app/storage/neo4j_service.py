"""
Neo4j knowledge graph storage service.
"""

import os
import logging
from typing import Any

from neo4j import GraphDatabase, Driver

logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI") or "bolt://localhost:7687"
NEO4J_USER = os.getenv("NEO4J_USER") or "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") or "password"


class Neo4jService:
    """Service for interacting with the Neo4j graph database."""

    def __init__(self, uri: str | None = None, user: str | None = None, password: str | None = None):
        self._uri = uri or NEO4J_URI
        self._user = user or NEO4J_USER
        self._password = password or NEO4J_PASSWORD
        self._driver: Driver | None = None
        
        try:
            self._driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))
            logger.info("Initialized Neo4j driver at %s", self._uri)
        except Exception as e:
            logger.error("Failed to initialize Neo4j driver: %s", e)
            raise

    def close(self):
        """Close the Neo4j driver connection."""
        if self._driver is not None:
            self._driver.close()

    def initialize_constraints(self) -> None:
        """Create uniqueness constraints on Document, Chunk, and Entity nodes."""
        queries = [
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
        ]
        
        with self._driver.session() as session:
            for query in queries:
                session.run(query)
        logger.info("Neo4j constraints initialized.")

    def sync_document_chunk(
        self,
        document_id: str,
        chunk_id: str,
        entities: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
        document_metadata: dict[str, Any] | None = None,
        chunk_metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Synchronize a chunk's entities and relationships into the graph.
        
        entities format: [{"id": "hash", "name": "...", "type": "..."}]
        relationships format: [{"source_id": "hash", "target_id": "hash", "type": "...", "description": "..."}]
        """
        if not self._driver:
            raise RuntimeError("Neo4j driver is not initialized.")
            
        doc_meta = document_metadata or {}
        chunk_meta = chunk_metadata or {}
            
        # We use a single transaction for atomicity per chunk
        with self._driver.session() as session:
            session.execute_write(
                self._upsert_graph_tx,
                document_id,
                chunk_id,
                entities,
                relationships,
                doc_meta,
                chunk_meta
            )
            
    @staticmethod
    def _upsert_graph_tx(
        tx, 
        document_id: str, 
        chunk_id: str, 
        entities: list[dict[str, Any]], 
        relationships: list[dict[str, Any]],
        doc_meta: dict[str, Any],
        chunk_meta: dict[str, Any]
    ):
        # 1. Ensure Document and Chunk nodes exist and link them
        tx.run(
            """
            MERGE (d:Document {id: $document_id})
            SET d += $doc_meta
            MERGE (c:Chunk {id: $chunk_id})
            SET c += $chunk_meta
            MERGE (d)-[:HAS_CHUNK]->(c)
            """,
            document_id=document_id,
            chunk_id=chunk_id,
            doc_meta=doc_meta,
            chunk_meta=chunk_meta
        )
        
        # 2. Upsert Entities and link Chunk -> Entity
        for entity in entities:
            tx.run(
                """
                MERGE (e:Entity {id: $ent_id})
                ON CREATE SET e.name = $name, e.type = $type
                MERGE (c:Chunk {id: $chunk_id})
                MERGE (c)-[:MENTIONS]->(e)
                """,
                ent_id=entity["id"],
                name=entity.get("name", ""),
                type=entity.get("type", "UNKNOWN"),
                chunk_id=chunk_id
            )
            
        # 3. Upsert Relationships between Entities
        for rel in relationships:
            # Note: Cypher doesn't allow dynamic relationship types in MERGE.
            # As planned, we use a generic RELATES_TO and store the actual semantic type as a property.
            tx.run(
                """
                MATCH (source:Entity {id: $source_id})
                MATCH (target:Entity {id: $target_id})
                MERGE (source)-[r:RELATES_TO {type: $rel_type}]->(target)
                ON CREATE SET r.description = $desc
                """,
                source_id=rel["source_id"],
                target_id=rel["target_id"],
                rel_type=rel.get("type", "RELATED"),
                desc=rel.get("description", "")
            )
