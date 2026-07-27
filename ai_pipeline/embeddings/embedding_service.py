"""
Embedding service.

Generates dense vector embeddings for text chunks using
the sentence-transformers library. The model is configurable
via environment variables.

In Phase 5, embeddings are generated but NOT persisted to Qdrant.
They will be stored in Qdrant during Phase 6.
"""

import os
import logging
from dataclasses import dataclass

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Configuration from environment
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL") or "all-MiniLM-L6-v2"
_env_dim = os.getenv("EMBEDDING_DIMENSION")
EMBEDDING_DIMENSION = int(_env_dim) if _env_dim else 384


@dataclass
class EmbeddingResult:
    """Result of embedding a batch of texts."""

    embeddings: list[list[float]]
    model_name: str
    dimension: int


class EmbeddingService:
    """
    Generates dense vector embeddings using sentence-transformers.

    The model is loaded lazily on first use and cached for reuse.
    """

    _model: SentenceTransformer | None = None

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or EMBEDDING_MODEL
        self._dimension = EMBEDDING_DIMENSION

    def _load_model(self) -> SentenceTransformer:
        """Load the embedding model (lazy initialization)."""
        if self._model is None:
            logger.info("Loading embedding model: %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)
            # Update dimension from the actual model
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(
                "Embedding model loaded: %s (dimension=%d)",
                self._model_name,
                self._dimension,
            )
        return self._model

    @property
    def model_name(self) -> str:
        """Return the configured model name."""
        return self._model_name

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimension

    def embed(self, texts: list[str], batch_size: int = 32) -> EmbeddingResult:
        """
        Generate embeddings for a list of text strings.

        Args:
            texts: List of text strings to embed.
            batch_size: Number of texts to process at once.

        Returns:
            EmbeddingResult containing the vectors and model metadata.
        """
        if not texts:
            return EmbeddingResult(
                embeddings=[],
                model_name=self._model_name,
                dimension=self._dimension,
            )

        model = self._load_model()

        logger.info("Generating embeddings for %d texts (batch_size=%d)...", len(texts), batch_size)
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        # Convert numpy arrays to plain Python lists
        embeddings_list = [vec.tolist() for vec in vectors]

        logger.info("Generated %d embeddings (dimension=%d).", len(embeddings_list), self._dimension)
        return EmbeddingResult(
            embeddings=embeddings_list,
            model_name=self._model_name,
            dimension=self._dimension,
        )
