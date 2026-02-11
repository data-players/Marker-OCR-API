"""
Full integration tests for Marker document parsing.
These tests verify the complete document parsing workflow with real Marker library.
Tests use actual PDF files from the test fixtures directory.

IMPORTANT: Models are loaded ONCE per module (module-scoped fixture) to avoid
memory exhaustion and segfaults from repeated model loading.
"""

import json
import pytest
import asyncio
from pathlib import Path
from app.services.document_parser import DocumentParserService
from app.services.file_handler import FileHandlerService


pytestmark = pytest.mark.fullstack


# Module-scoped fixtures: models loaded ONCE, shared across all tests
@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for the entire test module."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def document_parser(event_loop):
    """Create and initialize DocumentParserService once for all tests."""
    service = DocumentParserService()
    success = await service.initialize_models()
    assert success is True, "Failed to initialize Marker models"
    yield service
    await service.shutdown()


@pytest.fixture(scope="module")
def test_pdf_path():
    """Get path to test PDF file."""
    pdf_path = Path("/tests/backend/FullStack/file-to-parse/exemple_facture.pdf")
    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found at {pdf_path}")
    return pdf_path


class TestMarkerIntegration:
    """Real integration tests for Marker document processing."""

    @pytest.mark.asyncio
    async def test_models_are_ready(self, document_parser):
        """Test that Marker models are initialized and ready."""
        assert document_parser.models_ready is True
        assert document_parser.models_dict is not None

    @pytest.mark.asyncio
    async def test_parse_pdf_to_markdown(self, document_parser, test_pdf_path):
        """Test parsing real PDF to Markdown format with Marker."""
        result = await document_parser.parse_document(
            file_path=str(test_pdf_path),
            output_format="markdown"
        )

        assert result is not None
        assert isinstance(result, dict)

        # Markdown mode: text field should contain markdown content
        assert "text" in result, f"No text field in result: {result.keys()}"
        assert len(result["text"]) > 0, "Markdown text is empty"
        assert result["markdown_content"] is not None, "markdown_content should be set"
        assert result["rich_structure"] is None, "Markdown mode should not have rich_structure"

    @pytest.mark.asyncio
    async def test_parse_pdf_to_json(self, document_parser, test_pdf_path):
        """Test parsing real PDF to JSON format with Marker."""
        result = await document_parser.parse_document(
            file_path=str(test_pdf_path),
            output_format="json"
        )

        assert result is not None
        assert isinstance(result, dict)

        # rich_structure should be populated with JSON tree
        assert result.get("rich_structure") is not None, \
            "JSON mode should populate rich_structure"

        # text field must contain serialized JSON for LLM analysis
        text_content = result.get("text", "")
        assert len(text_content) > 0, \
            f"JSON mode must provide serialized JSON as text for LLM. Keys: {result.keys()}"

        # Verify text is valid JSON (serialized rich_structure)
        parsed_text = json.loads(text_content)
        assert isinstance(parsed_text, dict), "Text should be a serialized JSON structure"
        assert "block_type" in parsed_text, "Serialized JSON should contain block_type"

        # markdown_content should be None in JSON mode (no markdown generated)
        assert result.get("markdown_content") is None, \
            "JSON mode should not generate markdown_content"

    @pytest.mark.asyncio
    async def test_json_and_markdown_both_produce_content(self, document_parser, test_pdf_path):
        """Test that JSON and Markdown modes both produce non-empty content."""
        # Parse as markdown
        md_result = await document_parser.parse_document(
            file_path=str(test_pdf_path),
            output_format="markdown"
        )
        md_text = md_result.get("text", "")
        assert len(md_text.strip()) > 10, \
            f"Markdown text too short: '{md_text[:100]}'"

        # Parse as JSON
        json_result = await document_parser.parse_document(
            file_path=str(test_pdf_path),
            output_format="json"
        )
        json_text = json_result.get("text", "")
        assert len(json_text.strip()) > 10, \
            f"JSON text too short: '{json_text[:100]}'"
