"""
Combined analysis endpoint for one-shot document processing.
Orchestrates OCR processing and LLM analysis in a single API call.
"""

import uuid
import time
import json
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from app.core.logger import get_logger
from app.models.request_models import CombinedAnalysisRequest
from app.models.llm_models import (
    SchemaFieldDefinition,
    CombinedAnalysisResponse,
    CombinedJobStatus,
    CombinedAnalysisResult,
    CombinedAnalysisSyncResult
)
from app.models.response_models import ProcessingResult
from app.services.file_handler import FileHandlerService
from app.services.document_parser import DocumentParserService
from app.services.llm_service import LLMService
from app.services.redis_service import RedisService
from app.api.dependencies import (
    get_file_handler, 
    get_document_parser, 
    get_llm_service, 
    get_redis
)

logger = get_logger(__name__)

router = APIRouter(prefix="/combined", tags=["combined-analysis"])


@router.post("/analyze-url", response_model=CombinedAnalysisResponse)
async def analyze_document_from_url(
    request: CombinedAnalysisRequest,
    background_tasks: BackgroundTasks,
    file_handler: FileHandlerService = Depends(get_file_handler),
    document_parser: DocumentParserService = Depends(get_document_parser),
    llm_service: LLMService = Depends(get_llm_service),
    redis_service: RedisService = Depends(get_redis)
) -> CombinedAnalysisResponse:
    """
    Combined endpoint: Download document from URL, process with OCR, and analyze with LLM.
    
    This endpoint orchestrates both phases:
    1. Download and OCR processing (Marker)
    2. LLM analysis for structured data extraction
    
    ## Request Body Example
    
    ```json
    {
      "url": "https://example.com/invoice.pdf",
      "introduction": "Extract invoice information with line items",
      "schema": {
        "vendor_name": {
          "type": "string",
          "description": "Name of the vendor",
          "required": true
        },
        "invoice_number": {
          "type": "string",
          "description": "Invoice number",
          "required": true
        },
        "total_amount": {
          "type": "number",
          "description": "Total amount",
          "required": true
        },
        "line_items": {
          "type": "array",
          "description": "List of invoice line items with description and amount",
          "required": false
        },
        "vendor_address": {
          "type": "object",
          "description": "Vendor address details",
          "required": false,
          "properties": {
            "street": {
              "type": "string",
              "description": "Street address"
            },
            "city": {
              "type": "string",
              "description": "City name"
            },
            "postal_code": {
              "type": "string",
              "description": "Postal/ZIP code"
            }
          }
        }
      },
      "ocr_options": {
        "output_format": "markdown",
        "force_ocr": false
      }
    }
    ```
    
    ## Schema Field Types
    
    - **string**: Text data
    - **number**: Numeric values (float)
    - **integer**: Whole numbers
    - **boolean**: true/false
    - **array**: List of items (use `items` property to define array element schema)
    - **object**: Nested object (use `properties` property to define nested fields)
    
    ## Response
    
    Returns a job ID for tracking the combined OCR + LLM analysis progress.
    Use `GET /api/v1/combined/jobs/{combined_job_id}` to poll for results.
    
    Args:
        request: Combined analysis request with URL, schema, and options
        
    Returns:
        Response with combined_job_id for tracking overall progress
    """
    logger.info(f"Combined analysis request for URL: {request.url}")
    
    try:
        # Check if models are ready
        if not document_parser.models_ready:
            error_msg = "AI models are not loaded. Please wait for model initialization to complete."
            if document_parser.model_load_error:
                error_msg += f" Error: {document_parser.model_load_error}"
            logger.error(f"Processing rejected: {error_msg}")
            raise HTTPException(
                status_code=503,
                detail=error_msg
            )
        
        # Generate combined job ID
        combined_job_id = str(uuid.uuid4())
        
        # Serialize schema for storage
        schema_dict = {}
        for field_name, field_def in request.extraction_schema.items():
            if isinstance(field_def, SchemaFieldDefinition):
                schema_dict[field_name] = field_def.model_dump()
            elif isinstance(field_def, dict):
                schema_dict[field_name] = field_def
            else:
                # Convert to SchemaFieldDefinition for validation
                schema_dict[field_name] = SchemaFieldDefinition(**field_def).model_dump()
        
        # Store combined job status in Redis
        combined_job_data = {
            "combined_job_id": combined_job_id,
            "status": "pending",
            "url": request.url,
            "introduction": request.introduction,
            "schema": schema_dict,
            "created_at": time.time(),
            "updated_at": time.time(),
            "ocr_job_id": None,
            "analysis_id": None,
            "ocr_result": None,
            "final_result": None,
            "error_message": None,
            "current_phase": "pending"
        }
        
        # Store with a custom key for combined jobs
        redis_service.client.setex(
            f"combined_job:{combined_job_id}",
            86400,  # 24 hours TTL
            json.dumps(combined_job_data)
        )
        
        # Start background processing
        background_tasks.add_task(
            process_combined_analysis_background,
            combined_job_id,
            request.url,
            request.introduction,
            schema_dict,
            request.ocr_options,
            file_handler,
            document_parser,
            llm_service,
            redis_service
        )
        
        logger.info(f"Started combined analysis: {combined_job_id}")
        
        return CombinedAnalysisResponse(
            combined_job_id=combined_job_id,
            status="pending",
            message="Combined analysis started (OCR + LLM)",
            phases=["download", "ocr", "llm_analysis"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Combined analysis request failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Combined analysis request failed: {str(e)}"
        )


@router.post("/analyze-url-sync", response_model=CombinedAnalysisSyncResult)
async def analyze_document_from_url_sync(
    request: CombinedAnalysisRequest,
    file_handler: FileHandlerService = Depends(get_file_handler),
    document_parser: DocumentParserService = Depends(get_document_parser),
    llm_service: LLMService = Depends(get_llm_service)
) -> CombinedAnalysisSyncResult:
    """
    Synchronous combined endpoint: Download, OCR, and LLM analysis in one request.
    
    **WARNING**: This endpoint is blocking and may take 30 seconds to 2 minutes to complete.
    Use this for simpler workflows where you don't want to manage job polling.
    
    For long-running tasks or better user experience, use `/analyze-url` instead.
    
    ## Request Body Example
    
    ```json
    {
      "url": "https://example.com/invoice.pdf",
      "introduction": "Extract invoice information",
      "schema": {
        "vendor_name": {"type": "string", "description": "Vendor name", "required": true},
        "total_amount": {"type": "number", "description": "Total amount", "required": true}
      }
    }
    ```
    
    ## Response (Direct Result)
    
    ```json
    {
      "extracted_data": {
        "vendor_name": "ACME Corporation",
        "total_amount": 1375.00
      },
      "ocr_result": "Full OCR text...",
      "processing_time": 45.23
    }
    ```
    
    Args:
        request: Combined analysis request with URL, schema, and options
        
    Returns:
        Direct result with extracted data and OCR content
        
    Raises:
        HTTPException: If models not ready, processing fails, or timeout
    """
    logger.info(f"Synchronous combined analysis request for URL: {request.url}")
    
    start_time = time.time()
    
    try:
        # Check if models are ready
        if not document_parser.models_ready:
            error_msg = "AI models are not loaded. Please wait for model initialization."
            if document_parser.model_load_error:
                error_msg += f" Error: {document_parser.model_load_error}"
            logger.error(f"Processing rejected: {error_msg}")
            raise HTTPException(status_code=503, detail=error_msg)
        
        # Serialize schema
        schema_dict = {}
        for field_name, field_def in request.extraction_schema.items():
            if isinstance(field_def, SchemaFieldDefinition):
                schema_dict[field_name] = field_def.model_dump()
            elif isinstance(field_def, dict):
                schema_dict[field_name] = field_def
            else:
                schema_dict[field_name] = SchemaFieldDefinition(**field_def).model_dump()
        
        # PHASE 1: Download file
        logger.info(f"Phase 1/3: Downloading file from {request.url}")
        file_info = await file_handler.download_file_from_url(request.url)
        file_id = file_info["file_id"]
        file_path = await file_handler.get_file_path(file_id)
        logger.info(f"File downloaded: {file_id}")
        
        # PHASE 2: OCR Processing
        logger.info(f"Phase 2/3: Starting OCR processing")
        result = await document_parser.parse_document(
            file_path=str(file_path),
            output_format=request.ocr_options.output_format if request.ocr_options else "markdown",
            force_ocr=request.ocr_options.force_ocr if request.ocr_options else False,
            extract_images=request.ocr_options.extract_images if request.ocr_options else False,
            paginate_output=request.ocr_options.paginate_output if request.ocr_options else False,
            language=request.ocr_options.language if request.ocr_options else None
        )
        
        processing_result = ProcessingResult.from_marker_result(result)
        ocr_content = processing_result.content or processing_result.markdown_content
        
        if not ocr_content:
            raise HTTPException(status_code=500, detail="OCR processing returned empty content")
        
        logger.info(f"OCR completed, content length: {len(ocr_content)}")
        
        # PHASE 3: LLM Analysis
        logger.info(f"Phase 3/3: Starting LLM analysis")
        extracted_data = await llm_service.analyze_ocr_content(
            ocr_content=ocr_content,
            introduction=request.introduction,
            schema=schema_dict
        )
        
        total_time = time.time() - start_time
        logger.info(f"Synchronous combined analysis completed in {total_time:.2f}s")
        
        return CombinedAnalysisSyncResult(
            extracted_data=extracted_data,
            ocr_result=ocr_content,
            processing_time=total_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Synchronous combined analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Combined analysis failed: {str(e)}"
        )


@router.get("/jobs/{combined_job_id}", response_model=CombinedJobStatus)
async def get_combined_job_status(
    combined_job_id: str,
    redis_service: RedisService = Depends(get_redis)
) -> CombinedJobStatus:
    """
    Get status of a combined analysis job (simplified response).
    
    Returns a simplified job status with only essential fields:
    - job_id: Job identifier
    - extracted_data: Structured data extracted by LLM (available when completed)
    - ocr_result: Full OCR text content (available after OCR phase)
    - status: pending, processing, completed, or failed
    - current_phase: Current processing phase (downloading, ocr_processing, llm_analysis, etc.)
    - error_message: Error details if failed
    
    ## Response Example (Completed)
    
    ```json
    {
      "job_id": "a1b2c3d4-...",
      "extracted_data": {
        "vendor_name": "ACME Corporation",
        "invoice_number": "INV-2024-0123",
        "total_amount": 1375.00,
        "line_items": ["Consulting Services", "Software License"]
      },
      "ocr_result": "INVOICE\\n\\nACME Corporation\\n123 Business St...",
      "status": "completed",
      "current_phase": "completed",
      "error_message": null
    }
    ```
    
    Args:
        combined_job_id: Combined job identifier
        
    Returns:
        Simplified job status with essential fields only
    """
    logger.info(f"Combined job status request: {combined_job_id}")
    
    try:
        key = f"combined_job:{combined_job_id}"
        value = redis_service.client.get(key)
        
        if value is None:
            raise HTTPException(
                status_code=404,
                detail="Combined job not found"
            )
        
        job_data = json.loads(value)
        
        # Extract OCR result content (simplified)
        ocr_result_content = None
        if job_data.get("ocr_result") and isinstance(job_data["ocr_result"], dict):
            # Get the full content, not just the preview
            ocr_result_content = job_data["ocr_result"].get("content")
        
        # Extract extracted_data from final_result if completed
        extracted_data = None
        if job_data.get("final_result"):
            final_result = job_data["final_result"]
            if isinstance(final_result, dict):
                extracted_data = final_result.get("extracted_data")
                # If ocr_result is not set yet, get it from final_result
                if not ocr_result_content and final_result.get("ocr_content"):
                    ocr_result_content = final_result.get("ocr_content")
        
        return CombinedJobStatus(
            job_id=combined_job_id,
            extracted_data=extracted_data,
            ocr_result=ocr_result_content,
            status=job_data["status"],
            current_phase=job_data.get("current_phase"),
            error_message=job_data.get("error_message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get combined job status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )


async def process_combined_analysis_background(
    combined_job_id: str,
    url: str,
    introduction: str,
    schema: dict,
    ocr_options,
    file_handler: FileHandlerService,
    document_parser: DocumentParserService,
    llm_service: LLMService,
    redis_service: RedisService
):
    """
    Background task for combined OCR + LLM analysis.
    
    Orchestrates the full pipeline:
    1. Download document from URL
    2. Process with OCR (Marker)
    3. Extract structured data with LLM
    4. Store final result
    
    Args:
        combined_job_id: Combined job identifier
        url: Document URL
        introduction: LLM task introduction
        schema: Extraction schema
        ocr_options: OCR processing options
        file_handler: File handler service
        document_parser: Document parser service
        llm_service: LLM service
        redis_service: Redis service
    """
    start_time = time.time()
    
    def update_combined_job(updates: dict):
        """Helper to update combined job in Redis."""
        try:
            key = f"combined_job:{combined_job_id}"
            existing = redis_service.client.get(key)
            if existing:
                data = json.loads(existing)
                data.update(updates)
                data["updated_at"] = time.time()
                redis_service.client.setex(key, 86400, json.dumps(data))
        except Exception as e:
            logger.error(f"Failed to update combined job {combined_job_id}: {str(e)}")
    
    try:
        logger.info(f"Starting combined analysis background task: {combined_job_id}")
        
        # PHASE 1: Download file from URL
        update_combined_job({
            "status": "processing",
            "current_phase": "downloading"
        })
        logger.info(f"Phase 1/3: Downloading file from {url}")
        
        file_info = await file_handler.download_file_from_url(url)
        file_id = file_info["file_id"]
        file_path = await file_handler.get_file_path(file_id)
        
        logger.info(f"File downloaded: {file_id}")
        
        # PHASE 2: OCR Processing
        update_combined_job({
            "current_phase": "ocr_processing"
        })
        logger.info(f"Phase 2/3: Starting OCR processing")
        
        # Process document with OCR - respect user's format choice (JSON or Markdown)
        # document_parser handles text extraction for both formats via text_from_rendered
        result = await document_parser.parse_document(
            file_path=str(file_path),
            output_format=ocr_options.output_format if ocr_options else "markdown",
            force_ocr=ocr_options.force_ocr if ocr_options else False,
            extract_images=ocr_options.extract_images if ocr_options else False,
            paginate_output=ocr_options.paginate_output if ocr_options else False,
            language=ocr_options.language if ocr_options else None
        )
        
        # Convert to ProcessingResult
        processing_result = ProcessingResult.from_marker_result(result)
        ocr_content = processing_result.content or processing_result.markdown_content
        
        if not ocr_content:
            raise Exception("OCR processing returned empty content")
        
        logger.info(f"OCR processing completed, content length: {len(ocr_content)}")
        
        # Store OCR result
        update_combined_job({
            "current_phase": "ocr_completed",
            "ocr_result": {
                "content": ocr_content[:1000] + "..." if len(ocr_content) > 1000 else ocr_content,
                "full_length": len(ocr_content),
                "processing_time": processing_result.processing_time
            }
        })
        
        # PHASE 3: LLM Analysis
        update_combined_job({
            "current_phase": "llm_analysis"
        })
        logger.info(f"Phase 3/3: Starting LLM analysis")
        
        # Call LLM service
        extracted_data = await llm_service.analyze_ocr_content(
            ocr_content=ocr_content,
            introduction=introduction,
            schema=schema
        )
        
        total_processing_time = time.time() - start_time
        
        logger.info(f"LLM analysis completed in {total_processing_time:.2f}s")
        
        # Store final result
        update_combined_job({
            "status": "completed",
            "current_phase": "completed",
            "final_result": {
                "extracted_data": extracted_data,
                "ocr_content": ocr_content,
                "total_processing_time": total_processing_time,
                "ocr_processing_time": processing_result.processing_time,
                "llm_processing_time": total_processing_time - processing_result.processing_time
            }
        })
        
        logger.info(f"Combined analysis completed: {combined_job_id}")
        
    except Exception as e:
        logger.error(f"Combined analysis failed for {combined_job_id}: {str(e)}")
        
        update_combined_job({
            "status": "failed",
            "error_message": str(e)
        })

