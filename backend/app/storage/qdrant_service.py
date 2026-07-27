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
                # Note: Not verifying dimension here for simplicity, but in production we might.
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
