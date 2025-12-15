"""
Test configuration and fixtures for FullStack backend tests.
These tests require real Marker ML dependencies (no mocks).
"""

import asyncio
import pytest
import tempfile
from pathlib import Path

from app.core.config import settings
from app.services.file_handler import FileHandlerService
from app.services.document_parser import DocumentParserService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_pdf_bytes():
    """Generate sample PDF content for testing."""
    # Minimal valid PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj

xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000074 00000 n 
0000000120 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
199
%%EOF"""
    return pdf_content


@pytest.fixture
def file_handler_service():
    """Create a FileHandlerService instance with real dependencies."""
    # FullStack tests use real services
    service = FileHandlerService()
    return service


@pytest.fixture
def document_parser_service():
    """Create a DocumentParserService instance with real Marker dependencies."""
    # FullStack tests use real Marker service (no mocks)
    service = DocumentParserService()
    return service


@pytest.fixture
def temp_upload_dir():
    """Create a temporary directory for test file uploads."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)




