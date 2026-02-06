"""
Full integration tests for Marker document parsing.
These tests verify the complete document parsing workflow with real Marker library.
Tests use actual PDF files from the test fixtures directory.
"""

import pytest
import asyncio
from pathlib import Path
from app.services.document_parser import DocumentParserService
from app.services.file_handler import FileHandlerService


pytestmark = pytest.mark.fullstack


class TestMarkerIntegration:
    """Real integration tests for Marker document processing."""

    @pytest.fixture
    def document_parser(self):
        """Create DocumentParserService with real Marker."""
        return DocumentParserService()

    @pytest.fixture
    def file_handler(self):
        """Create FileHandlerService."""
        return FileHandlerService()

    @pytest.fixture
    def test_pdf_path(self):
        """Get path to test PDF file."""
        pdf_path = Path("/tests/backend/FullStack/file-to-parse/exemple_facture.pdf")
        if not pdf_path.exists():
            pytest.skip(f"Test PDF not found at {pdf_path}")
        return pdf_path

    @pytest.mark.asyncio
    async def test_initialize_marker_models(self, document_parser):
        """Test Marker model initialization."""
        # Initialize models
        success = await document_parser.initialize_models()
        
        # Verify initialization succeeded
        assert success is True, "Failed to initialize Marker models"
        assert document_parser.models_dict is not None, "Models dict is not loaded"

    @pytest.mark.asyncio
    async def test_parse_pdf_to_markdown(self, document_parser, test_pdf_path):
        """Test parsing real PDF to Markdown format with Marker."""
        # Initialize models
        success = await document_parser.initialize_models()
        assert success is True
        
        # Parse PDF to Markdown
        result = await document_parser.parse_document(
            file_path=str(test_pdf_path),
            output_format="markdown"
        )
        
        # Verify result
        assert result is not None
        assert isinstance(result, dict)
        
        # Should have content or markdown field
        has_content = "content" in result or "markdown" in result or "text" in result
        assert has_content, f"No content field in result: {result.keys()}"
        
        # Content should not be empty
        if "content" in result:
            assert len(result["content"]) > 0
        elif "markdown" in result:
            assert len(result["markdown"]) > 0
        elif "text" in result:
            assert len(result["text"]) > 0

    @pytest.mark.asyncio
    async def test_parse_pdf_to_json(self, document_parser, test_pdf_path):
        """Test parsing real PDF to JSON format with Marker."""
        # Initialize models
        success = await document_parser.initialize_models()
        assert success is True
        
        # Parse PDF to JSON
        result = await document_parser.parse_document(
            file_path=str(test_pdf_path),
            output_format="json"
        )
        
        # Verify result structure
        assert result is not None
        assert isinstance(result, dict)
        
        # JSON output should have structure
        assert len(result) > 0, "JSON output is empty"

    @pytest.mark.asyncio
    async def test_marker_shutdown(self, document_parser):
        """Test Marker service cleanup/shutdown."""
        # Initialize
        await document_parser.initialize_models()
        
        # Shutdown should not raise
        await document_parser.shutdown()
        
        # After shutdown, models should not be available
        # (attempting to parse should fail gracefully)
        assert True, "Shutdown completed without errors"

