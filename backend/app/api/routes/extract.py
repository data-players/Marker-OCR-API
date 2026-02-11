"""
Public extraction endpoint using flow API keys.
Allows external systems to submit documents for processing without authentication.
"""

import asyncio
import json
import time
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logger import get_logger
from app.core.database import get_db, get_async_session_maker
from app.models.database_models import Flow, FlowExecution
from app.models.workspace_models import FlowExecutionResponse
from app.models.enums import OutputFormat
from app.models.request_models import ExtractRequest
from app.services.file_handler import FileHandlerService
from app.services.document_parser import DocumentParserService
from app.services.llm_service import LLMService
from app.services.redis_service import RedisService
from app.services.flow_service import FlowService
from app.api.dependencies import get_file_handler, get_document_parser, get_llm_service, get_redis, get_extraction_queue

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


@router.post("/{api_key}")
async def extract_async(
    api_key: str,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    file_handler: FileHandlerService = Depends(get_file_handler),
    document_parser: DocumentParserService = Depends(get_document_parser),
    llm_service: LLMService = Depends(get_llm_service),
    redis_service: RedisService = Depends(get_redis),
    extraction_queue = Depends(get_extraction_queue)
):
    """
    Execute extraction flow asynchronously using API key.
    
    Submit a document via URL or binary file to be processed.
    Supports two modes:
    - JSON (application/json): {"url": "https://..."}
    - Binary (application/octet-stream): Raw file content
    
    Args:
        api_key: Flow API key (mk_xxx format)
        
    Returns:
        Execution ID and URLs to check status and get results
    """
    import time as time_module
    start_time = time_module.time()
    
    # Detect content type and parse accordingly
    content_type = http_request.headers.get("content-type", "").lower()
    document_url = None
    file_content = None
    input_type = None
    input_source = None
    
    if "application/json" in content_type:
        # Parse JSON body with URL
        try:
            body = await http_request.json()
            request_obj = ExtractRequest(**body)
            if not request_obj.url:
                raise HTTPException(
                    status_code=400,
                    detail="'url' field is required in the JSON body"
                )
            document_url = request_obj.url
            input_type = "url"
            input_source = request_obj.url
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON: {str(e)}"
            )
    elif "application/octet-stream" in content_type:
        # Read binary file content
        file_content = await http_request.body()
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="No file content provided"
            )
        # Try to get filename from headers
        content_disposition = http_request.headers.get("content-disposition", "")
        filename = "document.pdf"
        if "filename=" in content_disposition:
            filename = content_disposition.split("filename=")[1].strip('"\'')
        input_type = "file"
        input_source = filename
    else:
        raise HTTPException(
            status_code=400,
            detail="Content-Type must be 'application/json' or 'application/octet-stream'"
        )
    
    logger.info(f"[TIMING] Starting extract request with {input_type}")
    
    # Get flow by API key
    flow = await get_flow_by_api_key(api_key, db)
    logger.info(f"[TIMING] Got flow: {time_module.time() - start_time:.3f}s")
    logger.info(f"Extract request for flow: {flow.name} ({flow.id})")
    
    # Check if models are ready
    if not document_parser.models_ready:
        raise HTTPException(
            status_code=503,
            detail="AI models are not ready. Please try again later."
        )
    
    logger.info(f"[TIMING] Models ready check: {time_module.time() - start_time:.3f}s")
    
    # Create execution record
    flow_service = FlowService(db)
    execution = await flow_service.create_execution(
        flow=flow,
        input_type=input_type,
        input_source=input_source
    )
    
    logger.info(f"[TIMING] Execution created: {time_module.time() - start_time:.3f}s")
    
    # Update status to pending
    await flow_service.update_execution(execution, status="pending")
    
    logger.info(f"[TIMING] Status updated: {time_module.time() - start_time:.3f}s")
    
    execution_id = execution.id
    flow_id = flow.id
    extraction_schema = flow.extraction_schema
    introduction = flow.introduction
    ocr_options = flow.ocr_options or {}
    
    # Commit execution to DB BEFORE enqueuing (worker uses separate session)
    await db.commit()
    
    logger.info(f"[TIMING] DB committed: {time_module.time() - start_time:.3f}s")
    
    # Enqueue job for processing (FIFO queue, only one at a time)
    job_data = {
        "execution_id": execution_id,
        "flow_id": flow_id,
        "document_url": document_url,
        "file_content": file_content.hex() if file_content else None,
        "file_name": input_source if input_type == "file" else None,
        "extraction_schema": extraction_schema,
        "introduction": introduction,
        "ocr_options": ocr_options
    }
    
    await extraction_queue.enqueue_job(job_data)
    
    logger.info(f"[TIMING] Total response time: {time_module.time() - start_time:.3f}s")
    
    # Build absolute URLs using the request's base URL
    base_url = str(http_request.base_url).rstrip('/')
    
    return {
        "execution_id": execution_id,
        "flow_id": flow_id,
        "status": "pending",
        "message": "Document submitted for processing",
        "status_url": f"{base_url}/api/v1/extract/{api_key}/status/{execution_id}",
        "results_url": f"{base_url}/api/v1/extract/{api_key}/executions/{execution_id}/results",
        "stream_url": f"{base_url}/api/v1/extract/{api_key}/executions/{execution_id}/stream"
    }


@router.post("/{api_key}/sync")
async def extract_sync(
    api_key: str,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    file_handler: FileHandlerService = Depends(get_file_handler),
    document_parser: DocumentParserService = Depends(get_document_parser),
    llm_service: LLMService = Depends(get_llm_service),
    redis_service: RedisService = Depends(get_redis),
    extraction_queue = Depends(get_extraction_queue)
):
    """
    Execute extraction synchronously - waits for results before returning.
    
    Submit a document via URL or binary file and wait for processing to complete.
    Supports two modes:
    - JSON (application/json): {"url": "https://..."}
    - Binary (application/octet-stream): Raw file content
    
    Args:
        api_key: Flow API key (mk_xxx format)
        
    Returns:
        Complete extraction results when ready (blocks until completion)
    """
    import time as time_module
    start_time = time_module.time()
    
    # Detect content type and parse accordingly (same as async)
    content_type = http_request.headers.get("content-type", "").lower()
    document_url = None
    file_content = None
    input_type = None
    input_source = None
    
    if "application/json" in content_type:
        try:
            body = await http_request.json()
            request_obj = ExtractRequest(**body)
            if not request_obj.url:
                raise HTTPException(
                    status_code=400,
                    detail="'url' field is required in the JSON body"
                )
            document_url = request_obj.url
            input_type = "url"
            input_source = request_obj.url
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON: {str(e)}"
            )
    elif "application/octet-stream" in content_type:
        file_content = await http_request.body()
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="No file content provided"
            )
        content_disposition = http_request.headers.get("content-disposition", "")
        filename = "document.pdf"
        if "filename=" in content_disposition:
            filename = content_disposition.split("filename=")[1].strip('"\'')
        input_type = "file"
        input_source = filename
    else:
        raise HTTPException(
            status_code=400,
            detail="Content-Type must be 'application/json' or 'application/octet-stream'"
        )
    
    # Get flow by API key
    flow = await get_flow_by_api_key(api_key, db)
    logger.info(f"Sync extract request for flow: {flow.name} ({flow.id})")
    
    # Check if models are ready
    if not document_parser.models_ready:
        raise HTTPException(
            status_code=503,
            detail="AI models are not ready. Please try again later."
        )
    
    # Create execution record
    flow_service = FlowService(db)
    execution = await flow_service.create_execution(
        flow=flow,
        input_type=input_type,
        input_source=input_source
    )
    
    await flow_service.update_execution(execution, status="pending")
    
    execution_id = execution.id
    flow_id = flow.id
    extraction_schema = flow.extraction_schema
    introduction = flow.introduction
    ocr_options = flow.ocr_options or {}
    
    # Commit execution to DB BEFORE enqueuing (worker uses separate session)
    await db.commit()
    
    # Enqueue job
    job_data = {
        "execution_id": execution_id,
        "flow_id": flow_id,
        "document_url": document_url,
        "file_content": file_content.hex() if file_content else None,
        "file_name": input_source if input_type == "file" else None,
        "extraction_schema": extraction_schema,
        "introduction": introduction,
        "ocr_options": ocr_options
    }
    
    await extraction_queue.enqueue_job(job_data)
    
    # Wait for job to complete (poll with FRESH sessions to see worker updates)
    max_wait = 600  # 10 minutes timeout
    poll_interval = 2  # 2 seconds between polls
    elapsed = 0
    
    logger.info(f"[SYNC] Waiting for execution {execution_id} to complete...")
    
    while elapsed < max_wait:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
        
        # Use a FRESH session for each poll to see worker's committed changes
        async with get_async_session_maker()() as poll_db:
            poll_service = FlowService(poll_db)
            execution = await poll_service.get_execution(execution_id)
            
            if not execution:
                logger.error(f"[SYNC] Execution {execution_id} not found in database!")
                raise HTTPException(
                    status_code=404,
                    detail="Execution not found"
                )
            
            current_status = execution.status
            logger.debug(f"[SYNC] Execution {execution_id} status: {current_status}")
            
            if current_status == "completed":
                processing_time = (time.time() - start_time)
                logger.info(f"[SYNC] Execution {execution_id} completed after {processing_time:.2f}s")
                return {
                    "execution_id": execution_id,
                    "status": "completed",
                    "extracted_data": execution.extracted_data,
                    "processing_time": processing_time,
                    "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
                }
            
            elif current_status == "failed":
                logger.error(f"[SYNC] Execution {execution_id} failed: {execution.error_message}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Extraction failed: {execution.error_message}"
                )
    
    # Timeout
    logger.error(f"[SYNC] Execution {execution_id} timeout after {max_wait}s")
    raise HTTPException(
        status_code=504,
        detail="Extraction timeout - processing took too long"
    )


@router.get("/{api_key}/status/{execution_id}")
async def get_extraction_status(
    api_key: str,
    execution_id: str,
    http_request: Request,
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
    
    # Build absolute URLs using the request's base URL
    base_url = str(http_request.base_url).rstrip('/')
    
    # Add URLs for navigation
    response["status_url"] = f"{base_url}/api/v1/extract/{api_key}/status/{execution_id}"
    response["stream_url"] = f"{base_url}/api/v1/extract/{api_key}/executions/{execution_id}/stream"
    
    if execution.status == "completed":
        response["results_url"] = f"{base_url}/api/v1/extract/{api_key}/executions/{execution_id}/results"
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


@router.get("/{api_key}/executions/{execution_id}/results")
async def get_extraction_results(
    api_key: str,
    execution_id: str,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get extraction results for a completed execution.
    
    Args:
        api_key: Flow API key
        execution_id: Execution ID
        
    Returns:
        Extracted data if completed, error if not ready or failed
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
    
    # Check status
    if execution.status == "pending" or execution.status == "processing":
        raise HTTPException(
            status_code=202,
            detail="Extraction still processing. Check status endpoint for progress."
        )
    
    if execution.status == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Extraction failed: {execution.error_message}"
        )
    
    if execution.status == "completed":
        return {
            "execution_id": execution.id,
            "status": "completed",
            "extracted_data": execution.extracted_data,
            "processing_time": execution.processing_time,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
        }
    
    raise HTTPException(
        status_code=400,
        detail=f"Unknown status: {execution.status}"
    )


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


async def process_extraction_with_download(
    execution_id: str,
    flow_id: str,
    document_url: Optional[str],
    file_content: Optional[bytes],
    file_name: Optional[str],
    extraction_schema: dict,
    introduction: Optional[str],
    ocr_options: dict,
    file_handler: FileHandlerService,
    document_parser: DocumentParserService,
    llm_service: LLMService,
    redis_service: RedisService
):
    """Background task to download/save and process extraction."""
    try:
        async with get_async_session_maker()() as db:
            flow_service = FlowService(db)
            
            try:
                # Step 0: Get file (either download from URL or save uploaded file)
                logger.info(f"Starting file retrieval for execution {execution_id}")
                
                if document_url:
                    # Download from URL
                    file_info = await file_handler.download_file_from_url(document_url)
                    file_id = file_info["file_id"]
                    logger.info(f"File downloaded for execution {execution_id}: {file_id}")
                elif file_content and file_name:
                    # Save uploaded file
                    file_info = await file_handler.save_uploaded_file(file_content, file_name)
                    file_id = file_info["file_id"]
                    logger.info(f"File saved for execution {execution_id}: {file_id}")
                else:
                    raise ValueError("Neither document_url nor file_content provided")
                
                
                # Update status to processing once file is downloaded
                execution = await flow_service.get_execution(execution_id)
                if execution:
                    await flow_service.update_execution(execution, status="processing")
                
                # Now process the extraction (passing the same db session)
                await process_extraction(
                    execution_id=execution_id,
                    flow_id=flow_id,
                    file_id=file_id,
                    extraction_schema=extraction_schema,
                    introduction=introduction,
                    ocr_options=ocr_options,
                    file_handler=file_handler,
                    document_parser=document_parser,
                    llm_service=llm_service,
                    redis_service=redis_service,
                    db=db,
                    flow_service=flow_service
                )
                
            except Exception as e:
                logger.error(f"Download/extraction failed for {execution_id}: {str(e)}", exc_info=True)
                
                try:
                    execution = await flow_service.get_execution(execution_id)
                    if execution:
                        await flow_service.update_execution(
                            execution=execution,
                            status="failed",
                            error_message=str(e)
                        )
                except Exception as db_error:
                    logger.error(f"Failed to update execution status in DB: {str(db_error)}")
                
                try:
                    redis_service.update_execution(execution_id, {
                        "status": "failed",
                        "error_message": str(e)
                    })
                except Exception as redis_error:
                    logger.error(f"Failed to update execution status in Redis: {str(redis_error)}")
            
            try:
                await db.commit()
            except Exception as commit_error:
                logger.error(f"Failed to commit transaction: {str(commit_error)}")
    
    except asyncio.CancelledError:
        logger.debug(f"Download/extraction task cancelled for execution {execution_id}")
        raise
    
    except Exception as outer_error:
        logger.error(f"Unexpected error in download/extraction task: {str(outer_error)}", exc_info=True)


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
    redis_service: RedisService,
    db: AsyncSession,
    flow_service: FlowService
):
    """Process extraction with OCR and LLM analysis."""
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
    
    # Initialize Redis with empty steps
    redis_service.store_execution(execution_id, {"steps": [], "current_step": None})
    
    # Step 1: Get file path
    update_step("📁 Chargement du fichier", "in_progress")
    file_path = await file_handler.get_file_path(file_id)
    update_step("📁 Chargement du fichier", "completed")
    
    # Extract OCR options - respect user's format choice (JSON or Markdown)
    # JSON mode: LLM receives serialized Marker JSON structure
    # Markdown mode: LLM receives raw Marker markdown
    output_format = OutputFormat(ocr_options.get("output_format", "markdown"))
    force_ocr = ocr_options.get("force_ocr", False)
    
    # Step 2: OCR Processing
    update_step("🔍 Traitement OCR", "in_progress")
    logger.info(f"Starting OCR for execution {execution_id}, format={output_format.value}")
    result = await document_parser.parse_document(
        file_path=str(file_path),
        output_format=output_format,
        force_ocr=force_ocr,
        step_callback=step_callback
    )
    update_step("🔍 Traitement OCR", "completed")
    
    ocr_content = result.get("text") or result.get("markdown_content") or ""
    
    if not ocr_content:
        logger.warning(f"Empty OCR content for execution {execution_id}")
    
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
