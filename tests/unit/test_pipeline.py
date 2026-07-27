"""
Unit tests for Phase 5 — AI Pipeline.

Tests document parsing, chunking, and the pipeline orchestrator
using mocks for MinIO and database operations.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from ai_pipeline.chunking.recursive_chunker import ChunkResult, RecursiveChunker
from ai_pipeline.parsing.base_parser import ParseResult
from ai_pipeline.parsing.docx_parser import DocxParser
from ai_pipeline.parsing.parser_factory import get_parser
from ai_pipeline.parsing.pdf_parser import PdfParser
from ai_pipeline.parsing.txt_parser import TxtParser


# =====================================================================
# Parser Tests
# =====================================================================


class TestTxtParser:
    """Tests for plain text parsing."""

    def test_parse_utf8(self):
        parser = TxtParser()
        result = parser.parse(b"Hello, world!\nThis is a test.")
        assert result.text == "Hello, world!\nThis is a test."
        assert result.page_count is None

    def test_parse_empty(self):
        parser = TxtParser()
        result = parser.parse(b"")
        assert result.text == ""

    def test_parse_latin1_fallback(self):
        # Latin-1 encoded text with non-UTF-8 byte
        parser = TxtParser()
        text_bytes = "café résumé".encode("latin-1")
        result = parser.parse(text_bytes)
        assert "caf" in result.text


class TestParserFactory:
    """Tests for the parser factory."""

    def test_get_pdf_parser(self):
        parser = get_parser("application/pdf")
        assert isinstance(parser, PdfParser)

    def test_get_docx_parser(self):
        parser = get_parser(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert isinstance(parser, DocxParser)

    def test_get_txt_parser(self):
        parser = get_parser("text/plain")
        assert isinstance(parser, TxtParser)

    def test_unsupported_mime_type(self):
        with pytest.raises(ValueError, match="Unsupported MIME type"):
            get_parser("image/png")


# =====================================================================
# Chunker Tests
# =====================================================================


class TestRecursiveChunker:
    """Tests for the recursive text chunker."""

    def test_chunk_basic(self):
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=10)
        text = "A" * 200
        results = chunker.chunk(text)
        assert len(results) > 1
        assert all(isinstance(r, ChunkResult) for r in results)
        assert results[0].chunk_index == 0
        assert results[1].chunk_index == 1

    def test_chunk_small_text(self):
        chunker = RecursiveChunker(chunk_size=1000, chunk_overlap=200)
        text = "Short text."
        results = chunker.chunk(text)
        assert len(results) == 1
        assert results[0].content == "Short text."
        assert results[0].chunk_index == 0

    def test_chunk_empty_text(self):
        chunker = RecursiveChunker()
        results = chunker.chunk("")
        assert results == []

    def test_chunk_preserves_order(self):
        chunker = RecursiveChunker(chunk_size=20, chunk_overlap=5)
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        results = chunker.chunk(text)
        for i, r in enumerate(results):
            assert r.chunk_index == i

    def test_chunk_token_count(self):
        chunker = RecursiveChunker(chunk_size=100, chunk_overlap=10)
        text = "Hello world. " * 50
        results = chunker.chunk(text)
        for r in results:
            assert r.token_count == len(r.content)


# =====================================================================
# Pipeline Service Tests (with mocks)
# =====================================================================


class TestPipelineService:
    """Tests for the pipeline orchestrator using mocks."""

    @pytest.mark.asyncio
    async def test_process_document_rejects_already_processing(self):
        """Verify that a document already in PROCESSING state is rejected."""
        from backend.app.models.document import Document, DocumentStatus

        mock_session = AsyncMock()

        with patch(
            "backend.app.services.pipeline_service.StorageService"
        ) as MockStorage, patch(
            "backend.app.services.pipeline_service.DocumentRepository"
        ) as MockDocRepo:
            mock_doc = MagicMock(spec=Document)
            mock_doc.status = DocumentStatus.PROCESSING
            mock_doc.id = uuid.uuid4()

            mock_repo_instance = MockDocRepo.return_value
            mock_repo_instance.get_document_by_id_and_user = AsyncMock(
                return_value=mock_doc
            )

            from backend.app.services.pipeline_service import PipelineService
            from fastapi import HTTPException

            pipeline = PipelineService(mock_session)

            with pytest.raises(HTTPException) as exc_info:
                await pipeline.process_document(mock_doc.id, uuid.uuid4())
            assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_process_document_not_found(self):
        """Verify that a missing document raises 404."""
        mock_session = AsyncMock()

        with patch(
            "backend.app.services.pipeline_service.StorageService"
        ), patch(
            "backend.app.services.pipeline_service.DocumentRepository"
        ) as MockDocRepo:
            mock_repo_instance = MockDocRepo.return_value
            mock_repo_instance.get_document_by_id_and_user = AsyncMock(
                return_value=None
            )

            from backend.app.services.pipeline_service import PipelineService
            from fastapi import HTTPException

            pipeline = PipelineService(mock_session)

            with pytest.raises(HTTPException) as exc_info:
                await pipeline.process_document(uuid.uuid4(), uuid.uuid4())
            assert exc_info.value.status_code == 404
