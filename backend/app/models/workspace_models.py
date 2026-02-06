"""
Pydantic models for workspace and flow requests/responses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# Workspace Models

class WorkspaceCreateRequest(BaseModel):
    """Request model for creating a workspace."""
    
    name: str = Field(
        min_length=1,
        max_length=255,
        description="Workspace name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Workspace description"
    )


class WorkspaceUpdateRequest(BaseModel):
    """Request model for updating a workspace."""
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New workspace name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="New description"
    )


class WorkspaceResponse(BaseModel):
    """Response model for workspace data."""
    
    id: str = Field(description="Workspace ID")
    name: str = Field(description="Workspace name")
    description: Optional[str] = Field(description="Workspace description")
    created_at: datetime = Field(description="Creation date")
    updated_at: datetime = Field(description="Last update date")
    flow_count: int = Field(default=0, description="Number of flows")
    
    model_config = ConfigDict(from_attributes=True)


class WorkspaceListResponse(BaseModel):
    """Response model for list of workspaces."""
    
    workspaces: List[WorkspaceResponse] = Field(description="List of workspaces")
    total: int = Field(description="Total number of workspaces")


# Flow Models

class FlowCreateRequest(BaseModel):
    """Request model for creating a flow."""
    
    name: str = Field(
        min_length=1,
        max_length=255,
        description="Flow name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Flow description"
    )
    extraction_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON schema defining fields to extract"
    )
    introduction: str = Field(
        default="",
        max_length=2000,
        description="Instructions for the LLM extraction"
    )
    ocr_options: Dict[str, Any] = Field(
        default_factory=lambda: {
            "output_format": "markdown",
            "force_ocr": False,
            "extract_images": False,
            "paginate_output": False
        },
        description="OCR processing options"
    )


class FlowUpdateRequest(BaseModel):
    """Request model for updating a flow."""
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New flow name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="New description"
    )
    extraction_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="New extraction schema"
    )
    introduction: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="New LLM instructions"
    )
    ocr_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="New OCR options"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Active status"
    )


class FlowResponse(BaseModel):
    """Response model for flow data."""
    
    id: str = Field(description="Flow ID")
    workspace_id: str = Field(description="Parent workspace ID")
    name: str = Field(description="Flow name")
    description: Optional[str] = Field(description="Flow description")
    api_key: str = Field(description="Unique API key for this flow")
    extraction_schema: Dict[str, Any] = Field(description="Extraction schema")
    introduction: str = Field(description="LLM instructions")
    ocr_options: Dict[str, Any] = Field(description="OCR options")
    is_active: bool = Field(description="Active status")
    created_at: datetime = Field(description="Creation date")
    updated_at: datetime = Field(description="Last update date")
    execution_count: int = Field(default=0, description="Number of executions")
    
    model_config = ConfigDict(from_attributes=True)


class FlowListResponse(BaseModel):
    """Response model for list of flows."""
    
    flows: List[FlowResponse] = Field(description="List of flows")
    total: int = Field(description="Total number of flows")


# Execution Models

class FlowExecutionResponse(BaseModel):
    """Response model for flow execution."""
    
    id: str = Field(description="Execution ID")
    flow_id: str = Field(description="Flow ID")
    input_type: str = Field(description="Input type (url or file)")
    input_source: str = Field(description="Input source (URL or filename)")
    status: str = Field(description="Execution status")
    extracted_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extracted data"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )
    processing_time: Optional[float] = Field(
        default=None,
        description="Processing time in seconds"
    )
    created_at: datetime = Field(description="Creation date")
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Completion date"
    )
    
    model_config = ConfigDict(from_attributes=True)


class FlowExecutionListResponse(BaseModel):
    """Response model for list of executions."""
    
    executions: List[FlowExecutionResponse] = Field(description="List of executions")
    total: int = Field(description="Total number of executions")


# Public API Models

class ExtractUrlRequest(BaseModel):
    """Request model for extraction via URL."""
    
    url: str = Field(description="URL of the document to process")


class ExtractResponse(BaseModel):
    """Response model for extraction result."""
    
    execution_id: str = Field(description="Execution ID")
    status: str = Field(description="Execution status")
    extracted_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extracted data according to schema"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )
    processing_time: Optional[float] = Field(
        default=None,
        description="Processing time in seconds"
    )


# Async extraction models with step tracking

class ProcessingSubStep(BaseModel):
    """Sub-step within a processing step."""
    
    name: str = Field(description="Sub-step name")
    status: str = Field(default="pending", description="Sub-step status")
    start_time: Optional[float] = Field(default=None, description="Start timestamp")
    end_time: Optional[float] = Field(default=None, description="End timestamp")
    duration: Optional[float] = Field(default=None, description="Duration in seconds")


class ProcessingStep(BaseModel):
    """Processing step with status and timing."""
    
    name: str = Field(description="Step name")
    description: str = Field(description="Step description")
    status: str = Field(default="pending", description="Step status")
    start_time: Optional[float] = Field(default=None, description="Start timestamp")
    end_time: Optional[float] = Field(default=None, description="End timestamp")
    duration: Optional[float] = Field(default=None, description="Duration in seconds")
    sub_steps: List[ProcessingSubStep] = Field(
        default_factory=list,
        description="Sub-steps within this step"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")


class ExtractAsyncResponse(BaseModel):
    """Response model for async extraction initiation."""
    
    execution_id: str = Field(description="Execution ID for tracking")
    status: str = Field(description="Initial status (pending)")
    message: str = Field(description="Instructions message")
    status_url: str = Field(description="URL to poll for status")
    stream_url: str = Field(description="URL for SSE stream")


class ExecutionStatusResponse(BaseModel):
    """Response model for execution status with steps."""
    
    execution_id: str = Field(description="Execution ID")
    flow_id: str = Field(description="Flow ID")
    status: str = Field(description="Execution status")
    input_type: str = Field(description="Input type (url or file)")
    input_source: str = Field(description="Input source")
    created_at: float = Field(description="Creation timestamp")
    updated_at: float = Field(description="Last update timestamp")
    current_step: Optional[str] = Field(default=None, description="Current step name")
    steps: List[ProcessingStep] = Field(
        default_factory=list,
        description="Processing steps with status"
    )
    ocr_content: Optional[str] = Field(
        default=None,
        description="OCR content preview (truncated)"
    )
    ocr_content_length: Optional[int] = Field(
        default=None,
        description="Full OCR content length"
    )
    extracted_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extracted data (when completed)"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message (when failed)"
    )
    processing_time: Optional[float] = Field(
        default=None,
        description="Total processing time in seconds"
    )
    completed_at: Optional[float] = Field(
        default=None,
        description="Completion timestamp"
    )
