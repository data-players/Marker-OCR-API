"""
Pydantic models for API responses.
Defines the structure of outgoing API responses.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class JobStatus(str, Enum):
    """Job processing status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Step processing status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SubStep(BaseModel):
    """Individual sub-step with timing information."""
    
    name: str = Field(description="Sub-step name")
    status: StepStatus = Field(default=StepStatus.PENDING, description="Sub-step status")
    start_time: Optional[float] = Field(
        default=None,
        description="Sub-step start timestamp (Unix time)"
    )
    end_time: Optional[float] = Field(
        default=None,
        description="Sub-step end timestamp (Unix time)"
    )
    duration: Optional[float] = Field(
        default=None,
        description="Sub-step duration in seconds"
    )


class ProcessingStep(BaseModel):
    """Individual processing step information."""
    
    name: str = Field(description="Step name")
    description: str = Field(description="Step description")
    status: StepStatus = Field(description="Step status")
    start_time: Optional[float] = Field(
        default=None,
        description="Step start timestamp (Unix time)"
    )
    end_time: Optional[float] = Field(
        default=None,
        description="Step end timestamp (Unix time)"
    )
    duration: Optional[float] = Field(
        default=None,
        description="Step duration in seconds"
    )
    sub_steps: Optional[List[str]] = Field(
        default=None,
        description="Sub-step details or progress messages (deprecated, use sub_steps_detailed)"
    )
    sub_steps_detailed: Optional[List[SubStep]] = Field(
        default=None,
        description="Detailed sub-steps with timing information"
    )
    current_sub_step: Optional[str] = Field(
        default=None,
        description="Current sub-step being processed"
    )
    
    def start(self):
        """Mark step as started."""
        import time
        self.status = StepStatus.IN_PROGRESS
        self.start_time = time.time()
    
    def complete(self):
        """Mark step as completed."""
        import time
        self.status = StepStatus.COMPLETED
        self.end_time = time.time()
        if self.start_time:
            self.duration = self.end_time - self.start_time
    
    def fail(self):
        """Mark step as failed."""
        import time
        self.status = StepStatus.FAILED
        self.end_time = time.time()
        if self.start_time:
            self.duration = self.end_time - self.start_time


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
    
    model_config = ConfigDict(extra="allow")
        
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
        description="Processing progress (0-100) - deprecated, use steps instead"
    )
    
    steps: Optional[List[ProcessingStep]] = Field(
        default=None,
        description="Detailed processing steps with timing information"
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