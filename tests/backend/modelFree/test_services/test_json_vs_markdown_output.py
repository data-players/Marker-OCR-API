"""
Tests for JSON vs Markdown output format handling.

Verifies that the extraction pipeline correctly handles both formats
and passes the native Marker output (JSON or Markdown) to the LLM.

Architecture:
- Markdown mode: LLM receives raw Markdown from Marker
- JSON mode: LLM receives serialized JSON structure from Marker
The user chooses the format, and the LLM processes whichever native output is selected.
"""

import json
import pytest
from unittest.mock import MagicMock

from app.models.request_models import OutputFormat
from app.models.response_models import ProcessingResult

pytestmark = [pytest.mark.unit, pytest.mark.modelfree]


class TestProcessingResultFromMarkerResult:
    """Test ProcessingResult creation from Marker results with different formats."""

    def test_markdown_result_has_content(self):
        """Markdown format: text = raw markdown, passed to LLM as-is."""
        marker_result = {
            "text": "# Hello\nThis is markdown content",
            "markdown_content": "# Hello\nThis is markdown content",
            "rich_structure": None,
            "metadata": {"page_count": 1},
            "images": [],
            "processing_time": 1.5
        }

        result = ProcessingResult.from_marker_result(marker_result)

        assert result.content == "# Hello\nThis is markdown content"
        assert result.markdown_content == "# Hello\nThis is markdown content"
        assert result.rich_structure is None
        assert result.processing_time == 1.5

    def test_json_result_has_serialized_json_as_text(self):
        """JSON format: text = serialized JSON structure, passed to LLM."""
        json_structure = {
            "block_type": "Document",
            "children": [{"block_type": "Page", "children": []}]
        }
        # Simulate what document_parser does: json.dumps(rich_structure)
        serialized_json = json.dumps(json_structure, indent=2, ensure_ascii=False)

        marker_result = {
            "text": serialized_json,
            "markdown_content": None,
            "rich_structure": json_structure,
            "metadata": {"page_count": 1},
            "images": [],
            "processing_time": 2.0
        }

        result = ProcessingResult.from_marker_result(marker_result)

        assert result.content == serialized_json
        assert result.markdown_content is None
        assert result.rich_structure is not None
        assert result.rich_structure["block_type"] == "Document"
        # Verify the text is valid JSON parseable by LLM
        parsed = json.loads(result.content)
        assert parsed["block_type"] == "Document"

    def test_json_result_empty_structure_detected(self):
        """
        JSON format with empty/None rich_structure should produce empty text.
        This was the original bug: text was '' and markdown_content was None.
        """
        marker_result = {
            "text": "",
            "markdown_content": None,
            "rich_structure": None,
            "metadata": {},
            "images": [],
            "processing_time": 1.0
        }

        result = ProcessingResult.from_marker_result(marker_result)

        assert result.content == ""
        assert result.markdown_content is None
        assert result.rich_structure is None


class TestOcrContentExtraction:
    """Test the OCR content extraction patterns used in extraction flows."""

    def test_or_pattern_with_markdown_content(self):
        """Markdown mode: the `or` pattern gets markdown text for LLM."""
        result = {
            "text": "# Document Title\nContent here",
            "markdown_content": "# Document Title\nContent here",
            "rich_structure": None
        }

        ocr_content = result.get("text") or result.get("markdown_content") or ""
        assert ocr_content == "# Document Title\nContent here"

    def test_or_pattern_with_json_serialized(self):
        """JSON mode: the `or` pattern gets serialized JSON for LLM."""
        json_structure = {"block_type": "Document", "children": []}
        serialized = json.dumps(json_structure, indent=2, ensure_ascii=False)

        result = {
            "text": serialized,
            "markdown_content": None,
            "rich_structure": json_structure
        }

        ocr_content = result.get("text") or result.get("markdown_content") or ""
        assert ocr_content == serialized
        # Verify it's valid JSON
        parsed = json.loads(ocr_content)
        assert parsed["block_type"] == "Document"

    def test_or_pattern_with_empty_text_falls_to_markdown(self):
        """The `or` pattern should fall through to markdown_content when text is empty."""
        result = {
            "text": "",
            "markdown_content": "Fallback content",
            "rich_structure": None
        }

        ocr_content = result.get("text") or result.get("markdown_content") or ""
        assert ocr_content == "Fallback content"

    def test_or_pattern_with_all_empty_returns_empty(self):
        """The `or` pattern should return empty when all fields are empty."""
        result = {
            "text": "",
            "markdown_content": None,
            "rich_structure": None
        }

        ocr_content = result.get("text") or result.get("markdown_content") or ""
        assert ocr_content == ""

    def test_old_get_pattern_bug_with_empty_text(self):
        """
        Demonstrates the bug with the old pattern:
        result.get("text", result.get("markdown_content", ""))
        returns empty string even when markdown_content exists.
        """
        result = {
            "text": "",  # Empty string - key exists!
            "markdown_content": "Actual content that should be used",
        }

        # OLD buggy pattern - returns "" because "text" key exists
        old_pattern = result.get("text", result.get("markdown_content", ""))
        assert old_pattern == ""  # This was the bug!

        # NEW fixed pattern - falls through to markdown_content
        new_pattern = result.get("text") or result.get("markdown_content") or ""
        assert new_pattern == "Actual content that should be used"


class TestProcessingResultContentAccess:
    """Test ProcessingResult content access patterns used in combined_analysis."""

    def test_content_or_markdown_with_markdown_format(self):
        """Markdown mode: content = markdown text for LLM."""
        result = ProcessingResult(
            content="# Title\nMarkdown content",
            markdown_content="# Title\nMarkdown content",
            rich_structure=None,
            metadata={},
            processing_time=1.0
        )

        ocr_content = result.content or result.markdown_content
        assert ocr_content == "# Title\nMarkdown content"

    def test_content_or_markdown_with_json_format(self):
        """JSON mode: content = serialized JSON for LLM."""
        json_structure = {"block_type": "Document", "children": []}
        serialized = json.dumps(json_structure, indent=2, ensure_ascii=False)

        result = ProcessingResult(
            content=serialized,
            markdown_content=None,
            rich_structure=json_structure,
            metadata={},
            processing_time=1.0
        )

        ocr_content = result.content or result.markdown_content
        assert ocr_content == serialized
        assert len(ocr_content) > 0
        # LLM receives valid JSON
        parsed = json.loads(ocr_content)
        assert parsed["block_type"] == "Document"

    def test_content_or_markdown_with_empty_content(self):
        """Processing result with empty content should fall through to markdown."""
        result = ProcessingResult(
            content="",
            markdown_content="Fallback from markdown_content",
            rich_structure=None,
            metadata={},
            processing_time=1.0
        )

        ocr_content = result.content or result.markdown_content
        assert ocr_content == "Fallback from markdown_content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
