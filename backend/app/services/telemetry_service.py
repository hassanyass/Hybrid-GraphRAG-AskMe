"""
Telemetry and Diagnostics Service.

Provides structured logging and tracking for the ingestion pipeline,
including chunk-level execution times, token usage, and SLM fallbacks.
"""

import logging
import time
from typing import Any

logger = logging.getLogger("hybrid_graph_rag.telemetry")


class TelemetryService:
    """Centralized service for logging pipeline diagnostics."""

    @staticmethod
    def log_document_upload(
        document_name: str,
        pages: int,
        words: int,
        chunks: int,
        embedding_time: float,
        graph_extraction_time: float,
        llm_calls: int,
        prompt_tokens: int,
        completion_tokens: int
    ) -> None:
        """Log summary metrics for a complete document upload."""
        report = (
            f"\n{'='*50}\n"
            f"Document: {document_name}\n"
            f"Pages: {pages}\n"
            f"Words: {words}\n"
            f"Chunks: {chunks}\n"
            f"Embedding Time: {embedding_time:.2f} seconds\n"
            f"Graph Extraction Time: {graph_extraction_time:.2f} seconds\n"
            f"LLM Calls: {llm_calls}\n"
            f"Prompt Tokens: {prompt_tokens}\n"
            f"Completion Tokens: {completion_tokens}\n"
            f"{'='*50}"
        )
        logger.info(report)

    @staticmethod
    def log_llm_request(
        stage: str,
        chunk_index: int,
        total_chunks: int,
        prompt_tokens: int,
        completion_tokens: int,
        latency: float,
        provider: str
    ) -> None:
        """Log metrics for a specific LLM request (e.g., SLM relationship fallback)."""
        logger.info(
            f"LLM Request | Stage: {stage} | Chunk: {chunk_index}/{total_chunks} | "
            f"Prompt Tokens: {prompt_tokens} | Completion Tokens: {completion_tokens} | "
            f"Latency: {latency:.2f}s | Provider: {provider}"
        )

    @staticmethod
    def log_chunk_processing(
        chunk_id: str,
        action: str,
        duration: float,
        status: str,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """Log general processing stages for a chunk (e.g., semantic chunking, embedding)."""
        meta_str = f" | {metadata}" if metadata else ""
        logger.info(f"Chunk Processing | Chunk ID: {chunk_id} | Action: {action} | Status: {status} | Duration: {duration:.2f}s{meta_str}")


def track_latency(action_name: str):
    """Decorator to automatically track and log the execution time of a function."""
    def decorator(func):
        import asyncio
        from functools import wraps

        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.time()
                result = await func(*args, **kwargs)
                duration = time.time() - start
                logger.info(f"Action: {action_name} | Duration: {duration:.2f}s")
                return result
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.info(f"Action: {action_name} | Duration: {duration:.2f}s")
                return result
            return sync_wrapper

    return decorator
