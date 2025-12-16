"""
Pydantic models for LLM analysis functionality.
Defines schema definition, analysis requests and responses.
"""

from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class SchemaFieldDefinition(BaseModel):
    """Definition of a single field in the extraction schema."""
    
    type: Literal["string", "number", "integer", "boolean", "array", "object", "null"] = Field(
        description="Field data type"
    )
    description: str = Field(
        description="Description of what information to extract for this field"
    )
    required: bool = Field(
        default=False,
        description="Whether this field is required"
    )
    items: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Schema for array items (if type is array)"
    )
    properties: Optional[Dict[str, "SchemaFieldDefinition"]] = Field(
        default=None,
        description="Nested properties (if type is object)"
    )


class LLMAnalysisRequest(BaseModel):
    """Request to analyze OCR content with LLM."""
    
    job_id: str = Field(
        description="Job ID of the completed OCR processing"
    )
    introduction: str = Field(
        default="",
        description="Optional introduction text explaining the extraction task to the LLM"
    )
    schema: Dict[str, SchemaFieldDefinition] = Field(
        description="JSON schema defining the expected structure with types and descriptions"
    )


class LLMAnalysisResponse(BaseModel):
    """Response from LLM analysis."""
    
    analysis_id: str = Field(
        description="Unique identifier for this analysis"
    )
    job_id: str = Field(
        description="Original OCR job ID"
    )
    status: str = Field(
        description="Analysis status (completed, failed, processing)"
    )
    extracted_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extracted structured data matching the schema"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if analysis failed"
    )
    processing_time: float = Field(
        default=0.0,
        description="Time taken for LLM analysis in seconds"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Analysis creation timestamp"
    )


class LLMAnalysisStatus(BaseModel):
    """Status of an LLM analysis job."""
    
    analysis_id: str = Field(
        description="Analysis identifier"
    )
    job_id: str = Field(
        description="Original OCR job ID"
    )
    status: str = Field(
        description="Current status"
    )
    progress: Optional[int] = Field(
        default=None,
        description="Progress percentage (0-100)"
    )
    extracted_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extracted data (if completed)"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message (if failed)"
    )

