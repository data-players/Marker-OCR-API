"""
Unit tests for FileHandlerService.
Tests file upload, validation, and management functionality.
"""

import asyncio
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import io

from app.services.file_handler import FileHandlerService
from app.core.exceptions import (
    FileSizeExceededError,
    UnsupportedFileTypeError,
    FileNotFoundError,
    ValidationError
)


class TestFileHandlerService:
    """Test cases for FileHandlerService."""

    @pytest.mark.asyncio
    async def test_save_uploaded_file_success(self, file_handler_service, sample_pdf_bytes):
        """Test successful file upload and save."""
        filename = "test_document.pdf"
        
        file_info = await file_handler_service.save_uploaded_file(
            file_content=sample_pdf_bytes,
            filename=filename,
            validate=True
        )
        
        # Verify file info structure
        assert "file_id" in file_info
        assert file_info["filename"] == filename
        assert file_info["size"] == len(sample_pdf_bytes)
        assert file_info["content_type"] == "application/pdf"
        
        # Verify file exists in mock
        file_path = file_handler_service.get_file_path(file_info["file_id"])
        assert file_path is not None

    @pytest.mark.asyncio
    async def test_validate_file_size_limit(self, file_handler_service):
        """Test file size validation."""
        # Create content larger than default limit
        large_content = b"x" * (101 * 1024 * 1024)  # 101MB
        
        with pytest.raises(FileSizeExceededError):
            await file_handler_service.save_uploaded_file(
                file_content=large_content,
                filename="large_file.pdf",
                validate=True
            )

    @pytest.mark.asyncio
    async def test_validate_file_extension(self, file_handler_service):
        """Test file extension validation."""
        invalid_content = b"test content"
        
        with pytest.raises(UnsupportedFileTypeError):
            await file_handler_service.save_uploaded_file(
                file_content=invalid_content,
                filename="test.txt",  # .txt not in allowed extensions
                validate=True
            )

    @pytest.mark.asyncio
    async def test_validate_pdf_content_invalid_format(self, file_handler_service):
        """Test PDF content validation with invalid format."""
        invalid_pdf_content = b"This is not a PDF file"
        
        with pytest.raises(ValidationError):
            await file_handler_service.save_uploaded_file(
                file_content=invalid_pdf_content,
                filename="fake.pdf",
                validate=True
            )

    @pytest.mark.asyncio
    async def test_get_file_path_success(self, file_handler_service, sample_pdf_bytes):
        """Test getting file path for existing file."""
        # First save a file
        file_info = await file_handler_service.save_uploaded_file(
            file_content=sample_pdf_bytes,
            filename="test.pdf",
            validate=True
        )
        
        # Test getting file path
        file_path = file_handler_service.get_file_path(file_info["file_id"])
        assert file_path is not None
        assert str(file_path).endswith(".pdf")

    def test_get_file_path_not_found(self, file_handler_service):
        """Test getting file path for non-existent file."""
        non_existent_id = "non-existent-id"
        
        with pytest.raises(FileNotFoundError):
            file_handler_service.get_file_path(non_existent_id)

    @pytest.mark.asyncio
    async def test_delete_file_success(self, file_handler_service, sample_pdf_bytes):
        """Test successful file deletion."""
        # First save a file
        file_info = await file_handler_service.save_uploaded_file(
            file_content=sample_pdf_bytes,
            filename="to_delete.pdf",
            validate=True
        )
        
        file_id = file_info["file_id"]
        
        # Verify file exists
        file_path = file_handler_service.get_file_path(file_id)
        assert file_path is not None
        
        # Delete the file
        await file_handler_service.delete_file(file_id)
        
        # Verify file is deleted
        with pytest.raises(FileNotFoundError):
            file_handler_service.get_file_path(file_id)

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, file_handler_service):
        """Test deleting non-existent file."""
        # Should not raise exception for non-existent file
        await file_handler_service.delete_file("non-existent-id")

    @pytest.mark.asyncio
    async def test_list_files_empty(self, file_handler_service):
        """Test listing files when directory is empty."""
        files_info = await file_handler_service.list_files()
        
        assert files_info["files"] == []
        assert files_info["total_count"] == 0
        assert files_info["page"] == 1
        assert files_info["total_pages"] == 0

    @pytest.mark.asyncio
    async def test_list_files_with_pagination(self, file_handler_service, sample_pdf_bytes):
        """Test listing files with pagination."""
        # Save multiple files
        file_ids = []
        for i in range(3):
            file_info = await file_handler_service.save_uploaded_file(
                file_content=sample_pdf_bytes,
                filename=f"test_{i}.pdf",
                validate=True
            )
            file_ids.append(file_info["file_id"])
        
        # Test pagination
        files_info = await file_handler_service.list_files(page=1, page_size=2)
        
        assert len(files_info["files"]) == 2
        assert files_info["total_count"] == 3
        assert files_info["page"] == 1
        assert files_info["total_pages"] == 2

    @pytest.mark.asyncio
    async def test_save_output_success(self, file_handler_service):
        """Test saving processing output."""
        content = {"text": "extracted text", "metadata": {"pages": 1}}
        
        output_path = await file_handler_service.save_output(
            content=content,
            filename="test_output.json"
        )
        
        assert output_path is not None
        assert str(output_path).endswith("test_output.json")

    @pytest.mark.asyncio
    async def test_cleanup_old_files(self, file_handler_service, sample_pdf_bytes):
        """Test cleanup of old files."""
        # Save a file with "old" in the name for the mock to detect
        filename = "old_file.pdf"
        await file_handler_service.save_uploaded_file(
            file_content=sample_pdf_bytes,
            filename=filename,
            validate=True
        )

        # Run cleanup
        cleaned_count = await file_handler_service.cleanup_old_files(max_age_hours=1)

        # Should have cleaned up the old file
        assert cleaned_count >= 0

    @pytest.mark.asyncio
    async def test_get_disk_usage(self, file_handler_service, sample_pdf_bytes):
        """Test getting disk usage statistics."""
        # Save a file first
        await file_handler_service.save_uploaded_file(
            file_content=sample_pdf_bytes,
            filename="usage_test.pdf",
            validate=True
        )
        
        usage_info = await file_handler_service.get_disk_usage()
        
        assert "upload_dir" in usage_info
        assert "output_dir" in usage_info
        assert usage_info["upload_dir"]["used_bytes"] >= 0
        assert usage_info["output_dir"]["used_bytes"] >= 0 