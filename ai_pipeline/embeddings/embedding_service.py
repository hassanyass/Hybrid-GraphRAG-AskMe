"""
Embedding service.

Generates dense vector embeddings for text chunks using
the FlagEmbedding library (BGE-M3). The model is configurable
via environment variables.

In Phase 5, embeddings are generated but NOT persisted to Qdrant.
They will be stored in Qdrant during Phase 6.
"""

import os
import logging
import time
from dataclasses import dataclass

from FlagEmbedding import BGEM3FlagModel

logger = logging.getLogger(__name__)

# Configuration from environment
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL") or "BAAI/bge-m3"
_env_dim = os.getenv("EMBEDDING_DIMENSION")
EMBEDDING_DIMENSION = int(_env_dim) if _env_dim else 1024
_env_max_len = os.getenv("EMBEDDING_MAX_LENGTH")
EMBEDDING_MAX_LENGTH = int(_env_max_len) if _env_max_len else 8192
_env_batch_size = os.getenv("EMBEDDING_BATCH_SIZE")
EMBEDDING_BATCH_SIZE = int(_env_batch_size) if _env_batch_size else 16
EMBEDDING_USE_FP16 = os.getenv("EMBEDDING_USE_FP16", "false").lower() == "true"


@dataclass
class EmbeddingResult:
    """Result of embedding a batch of texts."""

    embeddings: list[list[float]]
    model_name: str
    dimension: int


class EmbeddingService:
    """
    Generates dense vector embeddings using FlagEmbedding (BGE-M3).

    The model is loaded lazily on first use and cached for reuse.
    """

    _model: BGEM3FlagModel | None = None
    _model_lock = __import__("threading").Lock()

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or EMBEDDING_MODEL
        self._dimension = EMBEDDING_DIMENSION
        self._max_length = EMBEDDING_MAX_LENGTH
        self._use_fp16 = EMBEDDING_USE_FP16
        self._default_batch_size = EMBEDDING_BATCH_SIZE

    def _load_model(self) -> BGEM3FlagModel:
        """Load the embedding model (lazy initialization with thread lock)."""
        if self.__class__._model is None:
            with self.__class__._model_lock:
                if self.__class__._model is None:
                    logger.info("Embedding model initialization started")
                    self.__class__._model = BGEM3FlagModel(
                        self._model_name,
                        use_fp16=self._use_fp16
                    )
                    # The dimension is fixed to 1024 for BGE-M3 dense vectors
                    self._dimension = 1024
                    logger.info("Embedding model loaded")
        return self.__class__._model

    @property
    def model_name(self) -> str:
        """Return the configured model name."""
        return self._model_name

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimension

    def embed(self, texts: list[str], batch_size: int | None = None) -> EmbeddingResult:
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
        bs = batch_size if batch_size else self._default_batch_size

        logger.info("Embedding inference started")
        logger.info("Batch size: %d", bs)
        start_time = time.time()
        
        result = model.encode(
            texts,
            batch_size=bs,
            max_length=self._max_length
        )
        
        # model.encode returns a dict with "dense_vecs", "lexical_weights", "colbert_vecs"
        vectors = result["dense_vecs"]
        
        duration = time.time() - start_time
        logger.info("Embedding inference completed")
        logger.info("Encoding duration: %.2fs", duration)

        # Convert numpy arrays to plain Python lists
        embeddings_list = [vec.tolist() for vec in vectors]

        logger.info("Generated %d vectors (dimension=%d).", len(embeddings_list), self._dimension)
        return EmbeddingResult(
            embeddings=embeddings_list,
            model_name=self._model_name,
            dimension=self._dimension,
        )
