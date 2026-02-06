"""
Pydantic models for API request validation.
Defines the structure and validation rules for incoming requests.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
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
    
    @field_validator('language')
    @classmethod
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
        min_length=1,
        max_length=10,
        description="List of file IDs to process"
    )
    
    options: DocumentProcessRequest = Field(
        default_factory=DocumentProcessRequest,
        description="Processing options applied to all files"
    )
    
    @field_validator('file_ids')
    @classmethod
    def validate_file_ids(cls, v):
        """Validate file IDs format."""
        if not v:
            raise ValueError('At least one file ID is required')
        return v


class CombinedAnalysisRequest(BaseModel):
    """Request model for combined OCR + LLM analysis from URL."""
    
    url: str = Field(
        description="URL of the document to process",
        examples=["https://example.com/invoice.pdf"]
    )
    
    introduction: str = Field(
        default="",
        description="Introduction text explaining the extraction task to the LLM",
        examples=["Extract key invoice information including vendor details, line items, and totals"]
    )
    
    extraction_schema: dict = Field(
        description="JSON schema defining the expected structure for LLM extraction",
        examples=[{
            "vendor_name": {
                "type": "string",
                "description": "Name of the vendor/company",
                "required": True
            },
            "invoice_number": {
                "type": "string",
                "description": "Invoice reference number",
                "required": True
            },
            "total_amount": {
                "type": "number",
                "description": "Total invoice amount",
                "required": True
            },
            "line_items": {
                "type": "array",
                "description": "List of items with description and price",
                "required": False
            },
            "vendor_address": {
                "type": "object",
                "description": "Vendor address information",
                "required": False,
                "properties": {
                    "street": {"type": "string", "description": "Street address"},
                    "city": {"type": "string", "description": "City"},
                    "postal_code": {"type": "string", "description": "Postal code"}
                }
            }
        }]
    )
    
    ocr_options: Optional[DocumentProcessRequest] = Field(
        default_factory=DocumentProcessRequest,
        description="OCR processing options (output_format, force_ocr, etc.)"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://example.com/invoice.pdf",
                    "introduction": "Extract invoice information with line items and vendor address",
                    "schema": {
                        "vendor_name": {
                            "type": "string",
                            "description": "Name of the vendor",
                            "required": True
                        },
                        "invoice_number": {
                            "type": "string",
                            "description": "Invoice number",
                            "required": True
                        },
                        "total_amount": {
                            "type": "number",
                            "description": "Total amount",
                            "required": True
                        },
                        "line_items": {
                            "type": "array",
                            "description": "List of invoice line items",
                            "required": False
                        },
                        "vendor_address": {
                            "type": "object",
                            "description": "Vendor address details",
                            "required": False,
                            "properties": {
                                "street": {"type": "string", "description": "Street address"},
                                "city": {"type": "string", "description": "City name"},
                                "postal_code": {"type": "string", "description": "Postal/ZIP code"}
                            }
                        }
                    },
                    "ocr_options": {
                        "output_format": "markdown",
                        "force_ocr": False
                    }
                }
            ]
        }
    } 