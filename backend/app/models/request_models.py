"""
Pydantic models for API request validation.
Defines the structure and validation rules for incoming requests.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class ProcessingOptions(str, Enum):
    """Available document processing options."""
    FAST = "fast"
    ACCURATE = "accurate"
    OCR_ONLY = "ocr_only"


class OutputFormat(str, Enum):
    """Available output formats."""
    JSON = "json"
    MARKDOWN = "markdown"
    BOTH = "both"


class DocumentProcessRequest(BaseModel):
    """Request model for document processing."""
    
    processing_option: ProcessingOptions = Field(
        default=ProcessingOptions.ACCURATE,
        description="Processing quality option"
    )
    
    output_format: OutputFormat = Field(
        default=OutputFormat.BOTH,
        description="Desired output format"
    )
    
    force_ocr: bool = Field(
        default=False,
        description="Force OCR even if text is extractable"
    )
    
    extract_images: bool = Field(
        default=True,
        description="Extract and include images"
    )
    
    extract_tables: bool = Field(
        default=True,
        description="Extract and format tables"
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