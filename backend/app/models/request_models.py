"""
Pydantic models for API request validation.
Defines the structure and validation rules for incoming requests.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class OutputFormat(str, Enum):
    """Available output formats."""
    JSON = "json"
    MARKDOWN = "markdown"


class DocumentProcessRequest(BaseModel):
    """Request model for document processing."""
    
    output_format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN,
        description="Desired output format"
    )
    
    force_ocr: bool = Field(
        default=False,
        description="Force OCR even if text is extractable"
    )
    
    extract_images: bool = Field(
        default=False,
        description="Extract and include images"
    )
    
    paginate_output: bool = Field(
        default=False,
        description="Add page separators in output. When enabled, adds separators between pages in the markdown output."
    )
    
    language: Optional[str] = Field(
        default=None,
        description="Document language hint (ISO 639-1 code)"
    )
    
    @validator('language')
    def validate_language(cls, v):
        """Validate language code format."""
        if v is not None and v != 'auto' and len(v) != 2:
            raise ValueError('Language code must be 2 characters (ISO 639-1) or "auto"')
        return v


class FileUploadRequest(BaseModel):
    """Request model for file upload with processing options."""
    
    filename: str = Field(description="Original filename")
    
    options: DocumentProcessRequest = Field(
        default_factory=DocumentProcessRequest,
        description="Processing options"
    )


class JobStatusRequest(BaseModel):
    """Request model for job status check."""
    
    job_id: str = Field(description="Job identifier")


class BatchProcessRequest(BaseModel):
    """Request model for batch processing."""
    
    file_ids: List[str] = Field(
        min_items=1,
        max_items=10,
        description="List of file IDs to process"
    )
    
    options: DocumentProcessRequest = Field(
        default_factory=DocumentProcessRequest,
        description="Processing options applied to all files"
    )
    
    @validator('file_ids')
    def validate_file_ids(cls, v):
        """Validate file IDs format."""
        if not v:
            raise ValueError('At least one file ID is required')
        return v 