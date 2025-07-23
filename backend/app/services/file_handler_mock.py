"""
Mock file handler service for testing without real file operations.
Avoids permission issues and provides fast test execution.
"""

import asyncio
import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock

from app.core.logger import LoggerMixin
from app.core.exceptions import (
    FileSizeExceededError,
    UnsupportedFileTypeError,
    FileNotFoundError,
    ValidationError,
    FileProcessingError
)
from app.core.config import settings


class MockFileHandlerService(LoggerMixin):
    """Mock file handler service for testing."""
    
    def __init__(self):
        # Mock in-memory storage
        self._files: Dict[str, Dict[str, Any]] = {}
        self._outputs: Dict[str, Any] = {}
        
        # Mock directories
        self.upload_dir = Path("/tmp/mock_uploads")
        self.output_dir = Path("/tmp/mock_outputs")
        
        self.log_operation("Mock directories initialized", 
                         upload_dir=str(self.upload_dir), 
                         output_dir=str(self.output_dir))

    async def save_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        validate: bool = True
    ) -> Dict[str, Any]:
        """Mock save uploaded file - stores in memory."""
        if validate:
            await self._validate_file(file_content, filename)

        # Generate mock file info
        file_id = str(uuid.uuid4())
        file_extension = Path(filename).suffix.lower()
        safe_filename = f"{file_id}{file_extension}"
        
        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        file_info = {
            "file_id": file_id,
            "filename": filename,  # Use the correct key name
            "stored_filename": safe_filename,
            "file_path": str(self.upload_dir / safe_filename),
            "size": len(file_content),
            "hash": file_hash,
            "upload_timestamp": datetime.now(),
            "content_type": self._get_content_type(file_extension)
        }
        
        # Store in mock memory
        self._files[file_id] = {
            **file_info,
            "content": file_content
        }
        
        self.log_operation(
            "File saved successfully",
            file_id=file_id,
            filename=filename,
            size=len(file_content)
        )
        
        return file_info

    def get_file_path(self, file_id: str) -> Path:
        """Mock get file path - synchronous method."""
        if file_id not in self._files:
            raise FileNotFoundError(f"File with ID {file_id} not found")
        
        return Path(self._files[file_id]["file_path"])

    async def delete_file(self, file_id: str) -> None:
        """Mock delete file - removes from memory."""
        if file_id in self._files:
            del self._files[file_id]
            self.log_operation("File deleted", file_id=file_id)

    async def list_files(
        self, 
        page: int = 1, 
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Mock list files with pagination."""
        # Filter out .gitkeep and system files
        real_files = {
            fid: finfo for fid, finfo in self._files.items() 
            if not finfo["filename"].startswith('.')
        }
        
        total_count = len(real_files)
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        
        # Calculate pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        files_list = list(real_files.values())[start_idx:end_idx]
        
        # Format files for response
        formatted_files = []
        for file_info in files_list:
            formatted_files.append({
                "file_id": file_info["file_id"],
                "filename": file_info["filename"],
                "size": file_info["size"],
                "created_at": file_info["upload_timestamp"],
                "modified_at": file_info["upload_timestamp"],
                "content_type": file_info["content_type"]
            })
        
        return {
            "files": formatted_files,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }

    async def save_output(
        self,
        content: Any,
        filename: str,
        file_format: str = "json"
    ) -> Path:
        """Mock save output - stores in memory."""
        output_id = str(uuid.uuid4())
        output_path = self.output_dir / filename
        
        # Store in mock memory
        if isinstance(content, dict):
            serialized_content = json.dumps(content, indent=2)
        else:
            serialized_content = str(content)
            
        self._outputs[output_id] = {
            "path": str(output_path),
            "content": serialized_content,
            "format": file_format
        }
        
        self.log_operation("Output saved", filename=filename, format=file_format)
        return output_path

    async def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """Mock cleanup - simulates cleaning old files."""
        # For testing, we'll simulate removing some files
        files_before = len(self._files)
        
        # Simulate removal of "old" files (for testing purposes)
        old_files = [fid for fid, finfo in self._files.items() 
                    if "old" in finfo["filename"].lower()]
        
        for file_id in old_files:
            del self._files[file_id]
        
        cleaned_count = len(old_files)
        self.log_operation(f"Cleanup completed", cleaned_count=cleaned_count)
        return cleaned_count

    async def get_disk_usage(self) -> Dict[str, Any]:
        """Mock disk usage statistics."""
        # Calculate mock usage from in-memory storage
        total_upload_size = sum(len(f.get("content", b"")) for f in self._files.values())
        total_output_size = sum(len(str(o.get("content", "")).encode()) for o in self._outputs.values())
        
        return {
            "upload_dir": {
                "path": str(self.upload_dir),
                "used_bytes": total_upload_size,
                "used_mb": round(total_upload_size / (1024 * 1024), 2),
                "file_count": len(self._files)
            },
            "output_dir": {
                "path": str(self.output_dir),
                "used_bytes": total_output_size,
                "used_mb": round(total_output_size / (1024 * 1024), 2),
                "file_count": len(self._outputs)
            }
        }

    async def _validate_file(self, file_content: bytes, filename: str) -> None:
        """Mock file validation."""
        # Size validation
        max_size = getattr(settings, 'max_file_size_mb', 100) * 1024 * 1024
        if len(file_content) > max_size:
            raise FileSizeExceededError(len(file_content), max_size)
        
        # Extension validation - only PDF files are allowed for this test
        allowed_extensions = ['.pdf']
        file_extension = Path(filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise UnsupportedFileTypeError(filename, allowed_extensions)
        
        # Content validation for PDFs
        if file_extension == '.pdf':
            if not file_content.startswith(b'%PDF'):
                raise ValidationError(f"Invalid PDF file format: {filename}")

    def _get_content_type(self, file_extension: str) -> str:
        """Get content type from file extension."""
        content_types = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.json': 'application/json',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream') 