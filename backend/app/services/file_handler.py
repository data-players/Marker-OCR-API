"""
File handling service for uploads, validation, and storage management.
Manages file lifecycle with proper validation and cleanup.
"""

import os
import uuid
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any, BinaryIO
import aiofiles
from datetime import datetime

from app.core.logger import LoggerMixin
from app.core.config import settings
from app.core.exceptions import (
    ValidationError,
    UnsupportedFileTypeError,
    FileSizeExceededError,
    FileNotFoundError as CustomFileNotFoundError,
    FileProcessingError
)


class FileHandlerService(LoggerMixin):
    """Service responsible for file operations and management."""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.output_dir = Path(settings.output_dir)
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure upload and output directories exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_operation(
            "Directories initialized",
            upload_dir=str(self.upload_dir),
            output_dir=str(self.output_dir)
        )
    
    async def download_file_from_url(
        self,
        url: str,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Download file from URL and save it.
        
        Args:
            url: URL to download file from
            validate: Whether to perform validation
            
        Returns:
            Dictionary with file information
        """
        import httpx
        from urllib.parse import urlparse
        
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValidationError(f"Invalid URL format: {url}")
            
            if parsed_url.scheme not in ['http', 'https']:
                raise ValidationError(f"Unsupported URL scheme: {parsed_url.scheme}")
            
            # Extract filename from URL or use default
            filename = parsed_url.path.split('/')[-1] or 'document.pdf'
            if not filename or '.' not in filename:
                # Try to get filename from Content-Disposition header or use default
                filename = 'document.pdf'
            
            # Download file with timeout
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('content-type', '')
                if 'application/pdf' not in content_type and not filename.endswith('.pdf'):
                    # Try to determine from Content-Disposition header
                    content_disposition = response.headers.get('content-disposition', '')
                    if 'filename=' in content_disposition:
                        filename = content_disposition.split('filename=')[1].strip('"\'')
                
                file_content = response.content
                
                # Validate file size
                if len(file_content) > settings.max_file_size:
                    raise FileSizeExceededError(
                        len(file_content),
                        settings.max_file_size
                    )
                
                # Save file using existing method
                return await self.save_uploaded_file(file_content, filename, validate)
                
        except httpx.HTTPError as e:
            self.log_error(e, "URL download", url=url)
            raise FileProcessingError(f"Failed to download file from URL: {str(e)}")
        except Exception as e:
            self.log_error(e, "URL download", url=url)
            raise FileProcessingError(f"Failed to download file from URL: {str(e)}")
    
    async def save_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Save uploaded file to disk with validation.
        
        Args:
            file_content: File binary content
            filename: Original filename
            validate: Whether to perform validation
            
        Returns:
            Dictionary with file information
        """
        if validate:
            await self._validate_file(file_content, filename)
        
        # Generate unique file ID and path
        file_id = str(uuid.uuid4())
        file_extension = Path(filename).suffix.lower()
        safe_filename = f"{file_id}{file_extension}"
        file_path = self.upload_dir / safe_filename
        
        try:
            # Save file asynchronously
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Calculate file hash for integrity
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            file_info = {
                "file_id": file_id,
                "original_filename": filename,
                "stored_filename": safe_filename,
                "file_path": str(file_path),
                "size": len(file_content),
                "hash": file_hash,
                "upload_timestamp": datetime.now(),
                "content_type": self._get_content_type(file_extension)
            }
            
            self.log_operation(
                "File saved successfully",
                file_id=file_id,
                filename=filename,
                size=len(file_content)
            )
            
            return file_info
            
        except Exception as e:
            # Clean up file if saving failed
            if file_path.exists():
                file_path.unlink()
            
            self.log_error(e, "File save operation", filename=filename)
            raise FileProcessingError(f"Failed to save file: {str(e)}")
    
    async def _validate_file(self, file_content: bytes, filename: str) -> None:
        """Validate uploaded file size and type."""
        # Check file size
        if len(file_content) > settings.max_file_size:
            raise FileSizeExceededError(
                len(file_content), 
                settings.max_file_size
            )
        
        # Check file extension
        file_extension = Path(filename).suffix.lower()
        if file_extension not in settings.allowed_extensions:
            raise UnsupportedFileTypeError(
                filename, 
                settings.allowed_extensions
            )
        
        # Additional validation for PDF files
        if file_extension == '.pdf':
            await self._validate_pdf_content(file_content)
    
    async def _validate_pdf_content(self, file_content: bytes) -> None:
        """Validate PDF file content."""
        # Check PDF magic bytes
        if not file_content.startswith(b'%PDF-'):
            raise ValidationError("Invalid PDF file format")
        
        # Basic PDF structure validation
        if b'%%EOF' not in file_content:
            raise ValidationError("Incomplete PDF file")
    
    def _get_content_type(self, extension: str) -> str:
        """Get MIME type for file extension."""
        mime_types = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.md': 'text/markdown'
        }
        return mime_types.get(extension, 'application/octet-stream')
    
    async def get_file_path(self, file_id: str) -> Path:
        """Get file path by file ID."""
        # Find file with matching ID prefix
        for file_path in self.upload_dir.iterdir():
            if file_path.stem == file_id:
                return file_path
        
        raise CustomFileNotFoundError(file_id)
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete file by ID."""
        try:
            file_path = await self.get_file_path(file_id)
            file_path.unlink()
            
            self.log_operation("File deleted", file_id=file_id)
            return True
            
        except CustomFileNotFoundError:
            self.log_operation("File not found for deletion", file_id=file_id)
            return False
        except Exception as e:
            self.log_error(e, "File deletion", file_id=file_id)
            return False
    
    async def list_files(
        self, 
        page: int = 1, 
        per_page: int = 20
    ) -> Dict[str, Any]:
        """List uploaded files with pagination."""
        try:
            all_files = []
            
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    file_info = {
                        "file_id": file_path.stem,
                        "filename": file_path.name,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime)
                    }
                    all_files.append(file_info)
            
            # Sort by creation time (newest first)
            all_files.sort(key=lambda x: x["created_at"], reverse=True)
            
            # Apply pagination
            start = (page - 1) * per_page
            end = start + per_page
            paginated_files = all_files[start:end]
            
            return {
                "files": paginated_files,
                "total": len(all_files),
                "page": page,
                "per_page": per_page,
                "total_pages": (len(all_files) + per_page - 1) // per_page
            }
            
        except Exception as e:
            self.log_error(e, "File listing")
            raise FileProcessingError(f"Failed to list files: {str(e)}")
    
    async def save_output(
        self,
        content: str,
        filename: str,
        file_format: str = "json"
    ) -> Path:
        """Save processed output to disk."""
        output_filename = f"{filename}.{file_format}"
        output_path = self.output_dir / output_filename
        
        try:
            async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            self.log_operation(
                "Output saved",
                filename=output_filename,
                size=len(content)
            )
            
            return output_path
            
        except Exception as e:
            self.log_error(e, "Output save", filename=output_filename)
            raise FileProcessingError(f"Failed to save output: {str(e)}")
    
    async def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """Clean up old files to free disk space."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0
        
        for directory in [self.upload_dir, self.output_dir]:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                        except Exception as e:
                            self.log_error(
                                e, 
                                "File cleanup", 
                                file_path=str(file_path)
                            )
        
        self.log_operation(
            "File cleanup completed",
            cleaned_files=cleaned_count,
            max_age_hours=max_age_hours
        )
        
        return cleaned_count
    
    async def get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage statistics."""
        def get_directory_size(directory: Path) -> int:
            """Calculate total size of directory."""
            total_size = 0
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        
        upload_size = get_directory_size(self.upload_dir)
        output_size = get_directory_size(self.output_dir)
        
        return {
            "upload_directory": {
                "path": str(self.upload_dir),
                "size_bytes": upload_size,
                "size_mb": round(upload_size / (1024 * 1024), 2)
            },
            "output_directory": {
                "path": str(self.output_dir),
                "size_bytes": output_size,
                "size_mb": round(output_size / (1024 * 1024), 2)
            },
            "total_size_bytes": upload_size + output_size,
            "total_size_mb": round((upload_size + output_size) / (1024 * 1024), 2)
        } 