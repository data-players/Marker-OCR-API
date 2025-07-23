"""
Pydantic models for API responses.
Defines the structure of outgoing API responses.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class JobStatus(str, Enum):
    """Job processing status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(description="Error message")
    status_code: int = Field(description="HTTP status code")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Error timestamp"
    )


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(default="healthy", description="Service status")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Check timestamp"
    )
    services: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of dependent services"
    )


class FileUploadResponse(BaseModel):
    """Response after successful file upload."""
    
    file_id: str = Field(description="Unique file identifier")
    filename: str = Field(description="Original filename")
    size: int = Field(description="File size in bytes")
    upload_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Upload completion time"
    )


class MarkerProcessingResult(BaseModel):
    """Direct result from Marker processing - flexible format."""
    
    text: str = Field(description="Extracted text content from Marker")
    metadata: Union[str, Dict[str, Any]] = Field(description="Document metadata from Marker")
    images: Union[List[str], Dict[str, Any]] = Field(description="Extracted images from Marker")
    processing_time: float = Field(description="Processing time in seconds")


class ProcessingResult(BaseModel):
    """
    Flexible result model that can accommodate both simple and rich processing results.
    Compatible with different output formats from Marker processing.
    """
    content: str  # Text content (markdown for preview compatibility)
    markdown_content: Optional[str] = None  # Explicit markdown content for download
    rich_structure: Optional[Dict[str, Any]] = None  # Rich JSON structure from Marker native JSON
    images: Union[List[str], List[Dict[str, Any]], Dict[str, Any]] = []  # Flexible image format
    metadata: Dict[str, Any] = {}
    processing_time: float = 0.0
    
    class Config:
        # Allow extra fields for future extensibility
        extra = "allow"
        
    @classmethod
    def from_marker_result(cls, result_dict: Dict[str, Any]) -> "ProcessingResult":
        """Create ProcessingResult from Marker processing result."""
        # Handle different image formats
        images = result_dict.get("images", [])
        if isinstance(images, dict):
            # Convert dict format to list of dicts
            images = [{"name": k, **v} if isinstance(v, dict) else {"name": k, "data": v} 
                     for k, v in images.items()]
        elif isinstance(images, list) and images and isinstance(images[0], dict):
            # Already in the right format
            pass
        
        return cls(
            content=result_dict.get("text", ""),
            markdown_content=result_dict.get("markdown_content"),
            rich_structure=result_dict.get("rich_structure"),
            images=images,
            metadata=result_dict.get("metadata", {}),
            processing_time=result_dict.get("processing_time", 0.0)
        )


class JobResponse(BaseModel):
    """Job status and result response."""
    
    job_id: str = Field(description="Job identifier")
    status: JobStatus = Field(description="Current job status")
    
    created_at: datetime = Field(description="Job creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    progress: Optional[float] = Field(
        default=None,
        description="Processing progress (0-100)"
    )
    
    result: Optional[ProcessingResult] = Field(
        default=None,
        description="Processing result if completed"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )


class DocumentProcessResponse(BaseModel):
    """Response for document processing request."""
    
    job_id: str = Field(description="Job identifier for tracking")
    status: JobStatus = Field(description="Initial job status")
    estimated_time: Optional[int] = Field(
        default=None,
        description="Estimated processing time in seconds"
    )


class BatchProcessResponse(BaseModel):
    """Response for batch processing request."""
    
    batch_id: str = Field(description="Batch identifier")
    jobs: List[DocumentProcessResponse] = Field(
        description="Individual job information"
    )
    total_files: int = Field(description="Total number of files")


class FileListResponse(BaseModel):
    """Response for file listing."""
    
    files: List[Dict[str, Any]] = Field(
        description="List of uploaded files"
    )
    total: int = Field(description="Total number of files")
    page: int = Field(default=1, description="Current page")
    per_page: int = Field(default=20, description="Items per page")


class MetricsResponse(BaseModel):
    """Application metrics response."""
    
    total_documents_processed: int = Field(
        description="Total documents processed"
    )
    active_jobs: int = Field(description="Currently active jobs")
    average_processing_time: float = Field(
        description="Average processing time in seconds"
    )
    success_rate: float = Field(description="Success rate percentage")
    uptime: float = Field(description="Service uptime in seconds") 