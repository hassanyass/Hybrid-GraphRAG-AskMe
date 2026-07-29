"""
Qdrant vector storage service.
"""

import os
import uuid
import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from qdrant_client.http.exceptions import UnexpectedResponse

from backend.app.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)

# Qdrant configuration
QDRANT_HOST = os.getenv("QDRANT_HOST") or "localhost"
QDRANT_PORT = int(os.getenv("QDRANT_PORT") or "6333")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME") or "document_chunks"


class QdrantService:
    """Service for interacting with the Qdrant vector database."""

    def __init__(self, host: str | None = None, port: int | None = None, collection_name: str | None = None):
        self._host = host or QDRANT_HOST
        self._port = port or QDRANT_PORT
        self._collection_name = collection_name or QDRANT_COLLECTION_NAME
        
        try:
            self._client = QdrantClient(host=self._host, port=self._port)
            logger.info("Initialized QdrantClient at %s:%d", self._host, self._port)
        except Exception as e:
            logger.error("Failed to initialize QdrantClient: %s", e)
            raise

    def ensure_collection(self, dimension: int) -> None:
        """
        Ensure the target collection exists with the correct vector size.
        If it doesn't exist, create it.
        """
        try:
            collections = self._client.get_collections()
            if any(c.name == self._collection_name for c in collections.collections):
                logger.debug("Qdrant collection '%s' already exists.", self._collection_name)
                
                # Verify dimension
                collection_info = self._client.get_collection(self._collection_name)
                vector_config = collection_info.config.params.vectors
                existing_dim = getattr(vector_config, 'size', None)
                if isinstance(vector_config, dict):
                    existing_dim = vector_config.get('size')
                
                if existing_dim and existing_dim != dimension:
                    logger.error(
                        "Dimension mismatch! Existing collection '%s' has dimension %s but model requires %d.", 
                        self._collection_name, existing_dim, dimension
                    )
                    if os.getenv("APP_ENV", "development").lower() == "development":
                        logger.warning("Development mode detected. Recreating collection '%s'...", self._collection_name)
                        self._client.delete_collection(self._collection_name)
                    else:
                        raise ValueError(
                            f"Qdrant dimension mismatch: Collection {self._collection_name} is {existing_dim}, "
                            f"but model needs {dimension}."
                        )
                else:
                    return
                
            logger.info("Creating Qdrant collection '%s' with dimension %d", self._collection_name, dimension)
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=rest.VectorParams(
                    size=dimension,
                    distance=rest.Distance.COSINE
                )
            )
        except UnexpectedResponse as e:
            logger.error("Failed to ensure Qdrant collection: %s", e)
            raise
        except Exception as e:
            logger.error("Unexpected error ensuring Qdrant collection: %s", e)
            raise

    def upsert_chunks(self, db_chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        """
        Synchronize chunk vectors to Qdrant.
        Vectors must map 1:1 with db_chunks by index.
        """
        if not db_chunks or not vectors:
            return
            
        if len(db_chunks) != len(vectors):
            raise ValueError(f"Mismatch: {len(db_chunks)} chunks vs {len(vectors)} vectors.")

        points = []
        for chunk, vector in zip(db_chunks, vectors):
            # Payload contains minimal retrieval metadata
            payload: dict[str, Any] = {
                "document_id": str(chunk.document_id),
                "chunk_index": chunk.chunk_index,
                "chunking_strategy": chunk.chunking_strategy,
            }
            if chunk.document and chunk.document.workspace_id:
                payload["workspace_id"] = str(chunk.document.workspace_id)
            if chunk.page_number is not None:
                payload["page_number"] = chunk.page_number
            if chunk.section_title is not None:
                payload["section_title"] = chunk.section_title
            if chunk.section_level is not None:
                payload["section_level"] = chunk.section_level
            if chunk.language is not None:
                payload["language"] = chunk.language

            points.append(
                rest.PointStruct(
                    id=str(chunk.id),  # Use UUID directly as Point ID
                    vector=vector,
                    payload=payload
                )
            )

        try:
            self._client.upsert(
                collection_name=self._collection_name,
                points=points,
                wait=True
            )
            logger.info("Upserted %d points to Qdrant collection '%s'", len(points), self._collection_name)
        except Exception as e:
            logger.error("Failed to upsert points to Qdrant: %s", e)
            raise

    def search(self, query_embedding: list[float], top_k: int = 5, workspace_id: str | None = None) -> list["VectorSearchResult"]:
        """
        Search for the most similar chunks to the query vector.
        Note: The returned results will not have chunk_text or filename 
        since they are not stored in Qdrant payloads. They must be enriched 
        by the caller from the relational database.
        """
        from backend.app.models.retrieval import VectorSearchResult
        
        try:
            query_filter = None
            if workspace_id:
                query_filter = rest.Filter(
                    must=[
                        rest.FieldCondition(
                            key="workspace_id",
                            match=rest.MatchValue(value=workspace_id)
                        )
                    ]
                )

            hits_response = self._client.query_points(
                collection_name=self._collection_name,
                query=query_embedding,
                query_filter=query_filter,
                limit=top_k
            )
            
            results = []
            for hit in hits_response.points:
                payload = hit.payload or {}
                results.append(
                    VectorSearchResult(
                        chunk_id=str(hit.id),
                        score=hit.score,
                        document_id=payload.get("document_id", ""),
                        page_number=payload.get("page_number"),
                        section_title=payload.get("section_title"),
                        chunk_index=payload.get("chunk_index", 0),
                        metadata=payload
                    )
                )
            logger.info("Qdrant search returned %d hits.", len(results))
            return results
        except Exception as e:
            logger.exception("Failed to search Qdrant: %s", e)
            return []
