"""
Public extraction endpoint using flow API keys.
Allows external systems to submit documents for processing without authentication.
"""

import asyncio
import json
import time
from typing import Optional, AsyncGenerator
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logger import get_logger
from app.core.database import get_db, get_async_session_maker
from app.models.database_models import Flow, FlowExecution
from app.models.workspace_models import FlowExecutionResponse
from app.models.enums import OutputFormat
from app.services.file_handler import FileHandlerService
from app.services.document_parser import DocumentParserService
from app.services.llm_service import LLMService
from app.services.redis_service import RedisService
from app.services.flow_service import FlowService
from app.api.dependencies import get_file_handler, get_document_parser, get_llm_service, get_redis

logger = get_logger(__name__)

router = APIRouter(prefix="/extract", tags=["extract"])


async def get_flow_by_api_key(api_key: str, db: AsyncSession) -> Flow:
    """Get flow by API key and verify it's active."""
    result = await db.execute(
        select(Flow).where(Flow.api_key == api_key, Flow.is_active == True)
    )
    flow = result.scalar_one_or_none()
    
    if not flow:
        raise HTTPException(
            status_code=404,
            detail="Flow not found or inactive"
        )
    
    return flow


@router.post("/{api_key}/async")
async def extract_async(
    api_key: str,
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    file_handler: FileHandlerService = Depends(get_file_handler),
    document_parser: DocumentParserService = Depends(get_document_parser),
    llm_service: LLMService = Depends(get_llm_service),
    redis_service: RedisService = Depends(get_redis)
):
    """
    Execute extraction flow asynchronously using API key.
    
    Submit a document (file upload or URL) to be processed with the flow's
    configured OCR options and extraction schema.
    
    Args:
        api_key: Flow API key (mk_xxx format)
        file: File to process (optional if url provided)
        url: URL to download document from (optional if file provided)
        
    Returns:
        Execution ID for tracking progress
    """
    # Validate input
    if not file and not url:
        raise HTTPException(
            status_code=400,
            detail="Either 'file' or 'url' must be provided"
        )
    
    if file and url:
        raise HTTPException(
            status_code=400,
            detail="Cannot provide both 'file' and 'url'"
        )
    
    # Get flow by API key
    flow = await get_flow_by_api_key(api_key, db)
    logger.info(f"Extract request for flow: {flow.name} ({flow.id})")
    
    # Check if models are ready
    if not document_parser.models_ready:
        raise HTTPException(
            status_code=503,
            detail="AI models are not ready. Please try again later."
        )
    
    # Handle file upload or URL download
    if url:
        logger.info(f"Downloading from URL: {url}")
        file_info = await file_handler.download_file_from_url(url)
        file_id = file_info["file_id"]
        input_source = url
        input_type = "url"
    else:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        content = await file.read()
        file_info = await file_handler.save_uploaded_file(content, file.filename)
        file_id = file_info["file_id"]
        input_source = file.filename
        input_type = "file"
    
    # Create execution record
    flow_service = FlowService(db)
    execution = await flow_service.create_execution(
        flow=flow,
        input_type=input_type,
        input_source=input_source
    )
    
    # Update status to processing
    await flow_service.update_execution(execution, status="processing")
    
    execution_id = execution.id
    flow_id = flow.id
    extraction_schema = flow.extraction_schema
    introduction = flow.introduction
    ocr_options = flow.ocr_options or {}
    
    # Start background processing using asyncio.create_task
    asyncio.create_task(
        process_extraction(
            execution_id=execution_id,
            flow_id=flow_id,
            file_id=file_id,
            extraction_schema=extraction_schema,
            introduction=introduction,
            ocr_options=ocr_options,
            file_handler=file_handler,
            document_parser=document_parser,
            llm_service=llm_service,
            redis_service=redis_service
        )
    )
    
    return {
        "execution_id": execution_id,
        "flow_id": flow_id,
        "status": "processing",
        "message": "Document submitted for processing"
    }


@router.get("/{api_key}/status/{execution_id}")
async def get_extraction_status(
    api_key: str,
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    redis_service: RedisService = Depends(get_redis)
):
    """
    Get status of an extraction execution.
    
    Args:
        api_key: Flow API key
        execution_id: Execution ID returned from extract_async
        
    Returns:
        Current status and results if complete
    """
    # Verify API key
    flow = await get_flow_by_api_key(api_key, db)
    
    # Get execution
    flow_service = FlowService(db)
    execution = await flow_service.get_execution(execution_id)
    
    if not execution or execution.flow_id != flow.id:
        raise HTTPException(
            status_code=404,
            detail="Execution not found"
        )
    
    response = {
        "execution_id": execution.id,
        "status": execution.status,
        "input_type": execution.input_type,
        "input_source": execution.input_source,
        "created_at": execution.created_at.isoformat() if execution.created_at else None
    }
    
    # Get steps from Redis
    redis_data = redis_service.get_execution(execution_id)
    if redis_data:
        response["steps"] = redis_data.get("steps", [])
        response["current_step"] = redis_data.get("current_step")
    
    if execution.status == "completed":
        response["extracted_data"] = execution.extracted_data
        response["processing_time"] = execution.processing_time
        response["completed_at"] = execution.completed_at.isoformat() if execution.completed_at else None
    elif execution.status == "failed":
        response["error_message"] = execution.error_message
    
    return response


async def stream_execution_status(
    api_key: str,
    execution_id: str
) -> AsyncGenerator[str, None]:
    """Stream execution status updates via SSE."""
    max_wait = 300  # 5 minutes max
    poll_interval = 1  # 1 second between polls
    elapsed = 0
    
    while elapsed < max_wait:
        async with get_async_session_maker()() as db:
            # Verify flow exists
            result = await db.execute(
                select(Flow).where(Flow.api_key == api_key, Flow.is_active == True)
            )
            flow = result.scalar_one_or_none()
            
            if not flow:
                yield f"data: {json.dumps({'error': 'Flow not found', 'done': True})}\n\n"
                return
            
            # Get execution
            flow_service = FlowService(db)
            execution = await flow_service.get_execution(execution_id)
            
            if not execution or execution.flow_id != flow.id:
                yield f"data: {json.dumps({'error': 'Execution not found', 'done': True})}\n\n"
                return
            
            status_data = {
                "execution_id": execution.id,
                "status": execution.status,
                "input_source": execution.input_source
            }
            
            if execution.status == "completed":
                status_data["extracted_data"] = execution.extracted_data
                status_data["processing_time"] = execution.processing_time
                status_data["done"] = True
                yield f"data: {json.dumps(status_data)}\n\n"
                # Small delay before closing to let client process the message
                await asyncio.sleep(0.1)
                return
            elif execution.status == "failed":
                status_data["error_message"] = execution.error_message
                status_data["done"] = True
                yield f"data: {json.dumps(status_data)}\n\n"
                # Small delay before closing to let client process the message
                await asyncio.sleep(0.1)
                return
            
            # Still processing
            yield f"data: {json.dumps(status_data)}\n\n"
        
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
    
    yield f"data: {json.dumps({'error': 'Timeout waiting for completion', 'done': True})}\n\n"


@router.get("/{api_key}/executions/{execution_id}/stream")
async def stream_extraction_status(
    api_key: str,
    execution_id: str
):
    """
    Stream execution status updates via Server-Sent Events (SSE).
    
    Args:
        api_key: Flow API key
        execution_id: Execution ID
        
    Returns:
        SSE stream with status updates
    """
    return StreamingResponse(
        stream_execution_status(api_key, execution_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


async def process_extraction(
    execution_id: str,
    flow_id: str,
    file_id: str,
    extraction_schema: dict,
    introduction: Optional[str],
    ocr_options: dict,
    file_handler: FileHandlerService,
    document_parser: DocumentParserService,
    llm_service: LLMService,
    redis_service: RedisService
):
    """Background task to process extraction."""
    start_time = time.time()
    steps = {}
    
    def update_step(step_name: str, status: str, step_time: float = None):
        """Update step status in Redis."""
        if step_name not in steps:
            steps[step_name] = {
                "name": step_name,
                "status": "pending",
                "start_time": None,
                "end_time": None,
                "duration": None
            }
        
        if status == "in_progress":
            steps[step_name]["status"] = "in_progress"
            steps[step_name]["start_time"] = time.time()
        elif status == "completed":
            steps[step_name]["status"] = "completed"
            steps[step_name]["end_time"] = time.time()
            if steps[step_name]["start_time"]:
                steps[step_name]["duration"] = steps[step_name]["end_time"] - steps[step_name]["start_time"]
        
        # Store in Redis
        redis_service.store_execution(execution_id, {
            "steps": list(steps.values()),
            "current_step": step_name if status == "in_progress" else None
        })
    
    async def step_callback(step_name: str, status: str, timestamp_or_substep = None):
        """Async callback for document parser steps."""
        update_step(step_name, status)
    
    async with get_async_session_maker()() as db:
        flow_service = FlowService(db)
        
        try:
            # Initialize Redis with empty steps
            redis_service.store_execution(execution_id, {"steps": [], "current_step": None})
            
            # Step 1: Get file path
            update_step("📁 Chargement du fichier", "in_progress")
            file_path = await file_handler.get_file_path(file_id)
            update_step("📁 Chargement du fichier", "completed")
            
            # Extract OCR options
            output_format = OutputFormat(ocr_options.get("output_format", "markdown"))
            force_ocr = ocr_options.get("force_ocr", False)
            
            # Step 2: OCR Processing
            update_step("🔍 Traitement OCR", "in_progress")
            logger.info(f"Starting OCR for execution {execution_id}")
            result = await document_parser.parse_document(
                file_path=str(file_path),
                output_format=output_format,
                force_ocr=force_ocr,
                step_callback=step_callback
            )
            update_step("🔍 Traitement OCR", "completed")
            
            ocr_content = result.get("text", result.get("markdown_content", ""))
            
            # Step 3: LLM Analysis
            update_step("🤖 Analyse LLM", "in_progress")
            logger.info(f"Starting LLM analysis for execution {execution_id}")
            extracted_data = await llm_service.analyze_ocr_content(
                ocr_content=ocr_content,
                introduction=introduction or "",
                schema=extraction_schema
            )
            update_step("🤖 Analyse LLM", "completed")
            
            # Update execution with results
            processing_time = time.time() - start_time
            execution = await flow_service.get_execution(execution_id)
            if execution:
                await flow_service.update_execution(
                    execution=execution,
                    status="completed",
                    extracted_data=extracted_data,
                    processing_time=processing_time
                )
            
            # Final update to Redis
            redis_service.update_execution(execution_id, {
                "status": "completed",
                "processing_time": processing_time
            })
            
            logger.info(f"Extraction completed for {execution_id} in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Extraction failed for {execution_id}: {str(e)}")
            
            execution = await flow_service.get_execution(execution_id)
            if execution:
                await flow_service.update_execution(
                    execution=execution,
                    status="failed",
                    error_message=str(e)
                )
            
            # Update Redis with error
            redis_service.update_execution(execution_id, {
                "status": "failed",
                "error_message": str(e)
            })
        
        await db.commit()
