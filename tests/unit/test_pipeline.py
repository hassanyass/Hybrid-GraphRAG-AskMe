"""
Unit tests for Phase 5 — AI Pipeline.

Tests document parsing, chunking, and the pipeline orchestrator
using mocks for MinIO and database operations.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from ai_pipeline.chunking.base_chunker import ChunkResult
from ai_pipeline.chunking.txt_chunker import TxtChunker
from ai_pipeline.chunking.pdf_chunker import PdfChunker
from ai_pipeline.chunking.docx_chunker import DocxChunker
from ai_pipeline.chunking.chunking_selector import ChunkingSelector
from ai_pipeline.parsing.base_parser import ParsedPage, ParseResult
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
        assert len(result.pages) == 1
        assert result.pages[0].page_number == 1
        assert result.page_count == 1

    def test_parse_empty(self):
        parser = TxtParser()
        result = parser.parse(b"")
        assert result.text == ""
        assert len(result.pages) == 0

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
# Hybrid Chunker Tests
# =====================================================================


class TestChunkingSelector:
    """Tests for strategy selection."""

    def test_get_chunker_pdf(self):
        chunker = ChunkingSelector.get_chunker("application/pdf")
        assert isinstance(chunker, PdfChunker)

    def test_get_chunker_docx(self):
        chunker = ChunkingSelector.get_chunker("application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        assert isinstance(chunker, DocxChunker)

    def test_get_chunker_txt(self):
        chunker = ChunkingSelector.get_chunker("text/plain")
        assert isinstance(chunker, TxtChunker)

    def test_get_chunker_fallback(self):
        chunker = ChunkingSelector.get_chunker("unknown/type")
        assert isinstance(chunker, TxtChunker)


class TestTxtChunker:
    """Tests for the text chunker."""

    def test_chunk_basic(self):
        chunker = TxtChunker(chunk_size=50, chunk_overlap=10)
        chunker._min_chunk_size = 1 # override min chunk size for testing
        pages = [ParsedPage(page_number=1, text="A" * 200)]
        results = chunker.chunk(pages)
        assert len(results) > 1
        assert all(isinstance(r, ChunkResult) for r in results)
        assert results[0].chunk_index == 0
        assert results[1].chunk_index == 1
        assert results[0].page_number == 1
        assert results[0].chunking_strategy == "txt_recursive"


class TestPdfChunker:
    """Tests for the PDF chunker."""

    def test_chunk_preserves_page_numbers(self):
        chunker = PdfChunker(chunk_size=50, chunk_overlap=10)
        chunker._min_chunk_size = 1 # override min chunk size for testing
        pages = [
            ParsedPage(page_number=1, text="Page one text. " * 5),
            ParsedPage(page_number=2, text="Page two text. " * 5),
        ]
        results = chunker.chunk(pages)
        assert len(results) > 1
        assert any(r.page_number == 1 for r in results)
        assert any(r.page_number == 2 for r in results)
        assert results[0].chunking_strategy == "pdf_recursive"


class TestDocxChunker:
    """Tests for the DOCX chunker."""

    def test_chunk_detects_headings(self):
        chunker = DocxChunker(chunk_size=1000, chunk_overlap=10)
        chunker._min_chunk_size = 1 # override min chunk size for testing
        pages = [
            ParsedPage(page_number=1, text="# Introduction\n\nThis is the intro.\n\n## Background\n\nSome background info.")
        ]
        results = chunker.chunk(pages)
        assert len(results) == 2
        
        # The intro chunk should have level 1 and title "Introduction"
        intro_chunk = results[0]
        assert intro_chunk.section_title == "Introduction"
        assert intro_chunk.section_level == 1
        
        # The background chunk should have level 2 and title "Background"
        bg_chunk = results[1]
        assert bg_chunk.section_title == "Background"
        assert bg_chunk.section_level == 2
        assert bg_chunk.chunking_strategy == "docx_heading_aware"


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
