"""
LLM Analysis endpoints for post-OCR structured data extraction.
Allows users to define schemas and extract structured data from OCR results.
"""

import uuid
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from app.core.logger import get_logger
from app.models.llm_models import (
    LLMAnalysisRequest,
    LLMAnalysisResponse,
    LLMAnalysisStatus
)
from app.models.response_models import JobStatus
from app.services.llm_service import LLMService
from app.services.redis_service import RedisService
from app.api.dependencies import get_llm_service, get_redis
from app.utils.validators import validate_job_id

logger = get_logger(__name__)

router = APIRouter(prefix="/llm", tags=["llm-analysis"])


@router.post("/analyze", response_model=LLMAnalysisResponse)
async def analyze_ocr_with_llm(
    request: LLMAnalysisRequest,
    background_tasks: BackgroundTasks,
    llm_service: LLMService = Depends(get_llm_service),
    redis_service: RedisService = Depends(get_redis)
):
    """
    Analyze OCR content with LLM to extract structured data.
    
    Args:
        request: Analysis request with job_id, introduction, and schema
        
    Returns:
        Analysis response with extracted structured data
    """
    logger.info(f"LLM analysis request for job: {request.job_id}")
    
    try:
        # Validate job_id format
        if not validate_job_id(request.job_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid job ID format"
            )
        
        # Get job data to retrieve OCR content
        job_data = redis_service.get_job(request.job_id)
        if job_data is None:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        
        # Check job is completed
        if job_data["status"] != JobStatus.COMPLETED.value:
            raise HTTPException(
                status_code=400,
                detail="OCR job must be completed before LLM analysis"
            )
        
        # Get OCR content from job result
        result = job_data.get("result")
        if not result:
            raise HTTPException(
                status_code=404,
                detail="No OCR result available for this job"
            )
        
        ocr_content = result.get("content") or result.get("markdown_content", "")
        if not ocr_content:
            raise HTTPException(
                status_code=400,
                detail="OCR content is empty"
            )
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Serialize schema for storage (convert Pydantic models to dict)
        schema_dict = {
            field_name: field_def.model_dump()
            for field_name, field_def in request.schema.items()
        }
        
        # Store analysis job in Redis
        analysis_data = {
            "analysis_id": analysis_id,
            "job_id": request.job_id,
            "status": "processing",
            "introduction": request.introduction,
            "schema": schema_dict,
            "created_at": time.time(),
            "updated_at": time.time(),
            "extracted_data": None,
            "error_message": None
        }
        redis_service.store_analysis(analysis_id, analysis_data)
        
        # Start background processing
        background_tasks.add_task(
            process_llm_analysis_background,
            analysis_id,
            request.job_id,
            ocr_content,
            request.introduction,
            schema_dict,
            llm_service,
            redis_service
        )
        
        logger.info(f"Started LLM analysis: {analysis_id}")
        
        return LLMAnalysisResponse(
            analysis_id=analysis_id,
            job_id=request.job_id,
            status="processing",
            extracted_data=None,
            error_message=None,
            processing_time=0.0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LLM analysis request failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis request failed: {str(e)}"
        )


@router.get("/analyze/{analysis_id}", response_model=LLMAnalysisStatus)
async def get_analysis_status(
    analysis_id: str,
    redis_service: RedisService = Depends(get_redis)
):
    """
    Get status of an LLM analysis.
    
    Args:
        analysis_id: Analysis identifier
        
    Returns:
        Analysis status with extracted data if completed
    """
    logger.info(f"Analysis status request: {analysis_id}")
    
    analysis_data = redis_service.get_analysis(analysis_id)
    if analysis_data is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )
    
    return LLMAnalysisStatus(
        analysis_id=analysis_id,
        job_id=analysis_data["job_id"],
        status=analysis_data["status"],
        progress=None,  # Could add progress tracking later
        extracted_data=analysis_data.get("extracted_data"),
        error_message=analysis_data.get("error_message")
    )


async def process_llm_analysis_background(
    analysis_id: str,
    job_id: str,
    ocr_content: str,
    introduction: str,
    schema: dict,
    llm_service: LLMService,
    redis_service: RedisService
):
    """
    Background task for LLM analysis processing.
    Updates analysis status and stores results in Redis.
    
    Args:
        analysis_id: Analysis identifier
        job_id: Original OCR job ID
        ocr_content: OCR text content
        introduction: User introduction
        schema: Extraction schema
        llm_service: LLM service instance
        redis_service: Redis service instance
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting LLM analysis background task: {analysis_id}")
        
        # Call LLM service
        extracted_data = await llm_service.analyze_ocr_content(
            ocr_content=ocr_content,
            introduction=introduction,
            schema=schema
        )
        
        processing_time = time.time() - start_time
        
        # Update analysis with result
        redis_service.update_analysis(analysis_id, {
            "status": "completed",
            "extracted_data": extracted_data,
            "processing_time": processing_time,
            "updated_at": time.time()
        })
        
        logger.info(f"LLM analysis completed: {analysis_id} (time: {processing_time:.2f}s)")
        
    except Exception as e:
        logger.error(f"LLM analysis failed for {analysis_id}: {str(e)}")
        
        # Update analysis with error
        redis_service.update_analysis(analysis_id, {
            "status": "failed",
            "error_message": str(e),
            "updated_at": time.time()
        })

