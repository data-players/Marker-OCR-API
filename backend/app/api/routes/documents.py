"""
Document processing endpoints for file upload and PDF conversion.
Main API routes for the document processing functionality.
"""

import uuid
import asyncio
from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks
from typing import Optional
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path

from app.core.logger import get_logger
from app.core.config import settings
from app.core.exceptions import BaseAPIException
from app.models import (
    DocumentProcessRequest,
    FileUploadResponse,
    DocumentProcessResponse,
    JobResponse,
    FileListResponse,
    JobStatus,
    ProcessingResult
)
from app.models.enums import OutputFormat
from app.services.file_handler import FileHandlerService
from app.services.document_parser import DocumentParserService
from app.services.redis_service import RedisService
from app.utils.validators import validate_filename, validate_job_id
from app.api.dependencies import get_file_handler, get_document_parser, get_redis

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    file_handler: FileHandlerService = Depends(get_file_handler)
):
    """
    Upload a file to the server.
    Can upload either a file directly or download from a URL.
    Returns file ID for subsequent processing.
    
    Args:
        file: File to upload (optional if url is provided)
        url: URL to download file from (optional if file is provided)
    """
    try:
        # Validate that either file or url is provided
        if not file and not url:
            raise HTTPException(
                status_code=400,
                detail="Either 'file' or 'url' must be provided"
            )
        
        if file and url:
            raise HTTPException(
                status_code=400,
                detail="Cannot provide both 'file' and 'url'. Please provide only one."
            )
        
        # Handle URL download
        if url:
            logger.info(f"Downloading file from URL: {url}")
            file_info = await file_handler.download_file_from_url(url)
            file_id = file_info["file_id"]
            filename = file_info["original_filename"]
            size = file_info["size"]
            
            logger.info(f"File downloaded from URL successfully: {file_id}")
            
            return FileUploadResponse(
                file_id=file_id,
                filename=filename,
                size=size,
                message="File downloaded from URL successfully"
            )
        
        # Handle file upload
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validate filename
        validate_filename(file.filename)
        
        # Validate file size
        content = await file.read()
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
            )
        
        # Save file and get file ID
        file_info = await file_handler.save_uploaded_file(content, file.filename)
        file_id = file_info["file_id"]
        
        logger.info(f"File uploaded successfully: {file_id}")
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            size=len(content),
            message="File uploaded successfully"
        )
        
    except BaseAPIException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/process", response_model=DocumentProcessResponse)
async def process_document(
    file_id: str = Form(...),
    output_format: OutputFormat = Form(OutputFormat.MARKDOWN),
    force_ocr: bool = Form(False),
    extract_images: bool = Form(False),
    paginate_output: bool = Form(False),
    language: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    file_handler: FileHandlerService = Depends(get_file_handler),
    document_parser: DocumentParserService = Depends(get_document_parser),
    redis_service: RedisService = Depends(get_redis)
):
    """
    Process an uploaded document.
    Starts background processing and returns job ID for tracking.
    """
    logger.info(f"Document processing request: {file_id}")
    
    try:
        # Check if models are ready - reject if not
        if not document_parser.models_ready:
            error_msg = "AI models are not loaded. Please wait for model initialization to complete."
            if document_parser.model_load_error:
                error_msg += f" Error: {document_parser.model_load_error}"
            logger.error(f"Processing rejected: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
        
        # Validate file exists
        file_path = await file_handler.get_file_path(file_id)
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create processing options object
        options = DocumentProcessRequest(
            output_format=output_format,
            force_ocr=force_ocr,
            extract_images=extract_images,
            paginate_output=paginate_output,
            language=language
        )
        
        # Store job status in Redis
        import time
        current_time = time.time()
        job_data = {
            "status": JobStatus.PENDING.value,
            "file_id": file_id,
            "created_at": current_time,
            "updated_at": current_time,
            "progress": 0,
            "steps": [],  # Initialize empty steps list
            "result": None,
            "error": None
        }
        redis_service.store_job(job_id, job_data)
        
        # Start background processing
        background_tasks.add_task(
            process_document_background,
            job_id,
            str(file_path),
            options,
            document_parser,
            file_handler,
            redis_service
        )
        
        logger.info(f"Started processing job: {job_id}")
        
        return DocumentProcessResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Document processing started"
        )
        
    except BaseAPIException:
        raise
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Processing request failed: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    redis_service: RedisService = Depends(get_redis)
):
    """
    Get processing job status and results.
    Returns current status and result if processing is complete.
    """
    logger.info(f"Job status request: {job_id}")
    
    if not validate_job_id(job_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid job ID format"
        )
    
    job_data = redis_service.get_job(job_id)
    if job_data is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    return JobResponse(
        job_id=job_id,
        status=JobStatus(job_data["status"]),
        created_at=job_data["created_at"],
        updated_at=job_data["updated_at"],
        progress=job_data.get("progress"),
        steps=job_data.get("steps"),
        result=job_data.get("result"),
        error_message=job_data.get("error_message")
    )


@router.get("/jobs/{job_id}/stream")
async def stream_job_status(
    job_id: str,
    redis_service: RedisService = Depends(get_redis)
):
    """
    Server-Sent Events (SSE) stream for real-time job status updates.
    Replaces polling with push-based updates using intelligent server-side polling.
    """
    import json as json_lib
    import time
    
    if not validate_job_id(job_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid job ID format"
        )
    
    # Verify job exists (with retry for race condition)
    # The job might be created just after the request, so we retry a few times
    import asyncio
    job_data = None
    for attempt in range(5):
        job_data = redis_service.get_job(job_id)
        if job_data:
            break
        await asyncio.sleep(0.1)  # Wait 100ms before retry
    
    if job_data is None:
        logger.warning(f"Job {job_id} not found after retries, but allowing SSE connection anyway")
        # Don't raise error - allow connection to establish and wait for job creation
    
    async def event_generator():
        """Generate SSE events with intelligent polling."""
        try:
            logger.debug(f"SSE event generator started for job {job_id}")
            import hashlib
            last_updated_at = None
            last_status = None
            last_steps_hash = None  # Hash of steps to detect content changes
            consecutive_no_change = 0
            max_no_change = 10  # Stop after 10 consecutive no-change polls
            
            # Send initial state immediately (with retry if job doesn't exist yet)
            initial_data = None
            for attempt in range(10):  # Wait up to 1 second for job creation
                initial_data = redis_service.get_job(job_id)
                if initial_data:
                    break
                await asyncio.sleep(0.1)
            
            if initial_data:
                logger.debug(f"Sending initial SSE data for job {job_id}: status={initial_data.get('status')}")
                event_data = json_lib.dumps({
                    "job_id": job_id,
                    "status": initial_data.get("status"),
                    "created_at": initial_data.get("created_at"),
                    "updated_at": initial_data.get("updated_at"),
                    "progress": initial_data.get("progress"),
                    "steps": initial_data.get("steps"),
                    "result": initial_data.get("result"),
                    "error_message": initial_data.get("error_message")
                })
                yield f"data: {event_data}\n\n"
                
                last_updated_at = initial_data.get("updated_at")
                last_status = initial_data.get("status")
                # Create hash of steps to detect content changes (like duration updates)
                steps_json = json_lib.dumps(initial_data.get("steps", []), sort_keys=True)
                last_steps_hash = hashlib.md5(steps_json.encode()).hexdigest()
                
                # If already completed/failed, close immediately
                if last_status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
                    logger.debug(f"Job {job_id} already finished, closing SSE stream")
                    return
            else:
                logger.warning(f"No initial data found for job {job_id} after retries, will wait for job creation")
                # Send a pending status to keep connection alive
                pending_event = json_lib.dumps({
                    "job_id": job_id,
                    "status": "pending",
                    "message": "Waiting for job to be created..."
                })
                yield f"data: {pending_event}\n\n"
            
            # Poll for updates
            while True:
                await asyncio.sleep(0.2)  # Poll every 200ms for real-time updates
                
                job_data = redis_service.get_job(job_id)
                if job_data is None:
                    # Job deleted or expired
                    error_event = json_lib.dumps({
                        "error": "Job not found",
                        "job_id": job_id
                    })
                    yield f"data: {error_event}\n\n"
                    break
                
                current_updated_at = job_data.get("updated_at")
                current_status = job_data.get("status")
                # Check if steps content changed (e.g., duration updates)
                current_steps_json = json_lib.dumps(job_data.get("steps", []), sort_keys=True)
                current_steps_hash = hashlib.md5(current_steps_json.encode()).hexdigest()
                
                # Check if there's a change (status, updated_at, or steps content)
                if (current_updated_at != last_updated_at or 
                    current_status != last_status or 
                    current_steps_hash != last_steps_hash):
                    # Data changed, send update
                    event_data = json_lib.dumps({
                        "job_id": job_id,
                        "status": current_status,
                        "created_at": job_data.get("created_at"),
                        "updated_at": current_updated_at,
                        "progress": job_data.get("progress"),
                        "steps": job_data.get("steps"),
                        "result": job_data.get("result"),
                        "error_message": job_data.get("error_message")
                    })
                    yield f"data: {event_data}\n\n"
                    
                    last_updated_at = current_updated_at
                    last_status = current_status
                    last_steps_hash = current_steps_hash
                    consecutive_no_change = 0
                    
                    # If job is completed/failed, close stream after a short delay
                    if current_status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
                        await asyncio.sleep(0.5)  # Small delay to ensure final update is sent
                        break
                else:
                    consecutive_no_change += 1
                    # Send keepalive more frequently to prevent connection timeout
                    # Browsers/proxies may close idle connections after 30-60 seconds
                    if consecutive_no_change >= 25:  # 5 seconds without change (200ms * 25)
                        yield f": keepalive\n\n"
                        consecutive_no_change = 0
                    
                    # Safety: stop if no change for too long (job might be stuck)
                    # But only if job is not processing (might be stuck in pending)
                    if consecutive_no_change >= max_no_change * 50 and current_status not in ['processing', 'pending']:
                        logger.warning(f"SSE stream timeout for job {job_id} - no changes detected, status={current_status}")
                        break
                
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for job {job_id}")
            raise
        except Exception as e:
            logger.error(f"SSE stream error for job {job_id}: {str(e)}")
            error_event = json_lib.dumps({
                "error": str(e),
                "job_id": job_id
            })
            yield f"data: {error_event}\n\n"
    
    logger.info(f"SSE stream initiated for job {job_id}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
            "Access-Control-Allow-Origin": "*",  # CORS for SSE
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.get("/files", response_model=FileListResponse)
async def list_files(
    page: int = 1,
    per_page: int = 20,
    file_handler: FileHandlerService = Depends(get_file_handler)
):
    """
    List uploaded files with pagination.
    """
    logger.info(f"File list request: page={page}, per_page={per_page}")
    
    try:
        files_data = await file_handler.list_files(page=page, per_page=per_page)
        
        return FileListResponse(
            files=files_data["files"],
            total=files_data["total"],
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"File listing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"File listing failed: {str(e)}"
        )


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    file_handler: FileHandlerService = Depends(get_file_handler)
):
    """
    Delete an uploaded file.
    """
    logger.info(f"File deletion request: {file_id}")
    
    try:
        success = await file_handler.delete_file(file_id)
        
        if success:
            return {"message": "File deleted successfully", "file_id": file_id}
        else:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion failed for {file_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"File deletion failed: {str(e)}"
        )


@router.get("/download/{job_id}")
async def download_result(
    job_id: str,
    format: str = "json",
    redis_service: RedisService = Depends(get_redis)
):
    """
    Download processed document result with full structure.
    Available formats: json, markdown
    """
    logger.info(f"Download request: {job_id}, format={format}")
    
    if not validate_job_id(job_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid job ID format"
        )
    
    job_data = redis_service.get_job(job_id)
    if job_data is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    if job_data["status"] != JobStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail="Job not completed yet"
        )
    
    if not job_data.get("result"):
        raise HTTPException(
            status_code=404,
            detail="No result available"
        )
    
    # Return the appropriate format
    result = job_data["result"]
    
    if format.lower() == "markdown":
        # Return markdown content
        markdown_content = result.markdown_content if hasattr(result, 'markdown_content') else result.content
        return {
            "job_id": job_id,
            "format": "markdown",
            "status": "completed",
            "content": markdown_content,
            "processing_time": result.processing_time if hasattr(result, 'processing_time') else 0,
            "message": "Markdown content ready for download"
        }
    else:
        # Return full result with JSON structure (default)
        return {
            "job_id": job_id,
            "format": "json",
            "status": "completed",
            "result": result,  # Full result with rich_structure
            "processing_time": result.processing_time if hasattr(result, 'processing_time') else 0,
            "message": "Document processed successfully"
        }


async def process_document_background(
    job_id: str,
    file_path: Path,
    options: DocumentProcessRequest,
    document_parser: DocumentParserService,
    file_handler: FileHandlerService,
    redis_service: RedisService
):
    """
    Background task for document processing.
    Updates job status and stores results in Redis.
    """
    import time
    from app.models.response_models import ProcessingStep, StepStatus, SubStep
    
    # Initialize processing steps
    steps_dict = {}
    
    # Initialize steps in Redis immediately (steps will be created dynamically as they are detected)
    redis_service.update_job(job_id, {
        "status": JobStatus.PROCESSING.value,
        "steps": [],
        "updated_at": time.time()
    })
    logger.info(f"Initialized processing job {job_id} - steps will be created dynamically")
    
    async def step_callback(step_name: str, status: str, timestamp: float = None):
        """Callback to update step status in Redis. All steps are independent (no sub-steps)."""
        import time
        
        # Debug: Log all step callbacks
        logger.info(f"📢 Step callback: {step_name} | status={status} | timestamp={timestamp}")
        
        # Create step if it doesn't exist (for dynamically created steps from tqdm/logs)
        if step_name not in steps_dict:
            logger.info(f"➕ Creating new step dynamically: {step_name}")
            # Create step dynamically with a generic description
            steps_dict[step_name] = ProcessingStep(
                name=step_name,
                description=step_name,  # Use name as description for dynamic steps
                status=StepStatus.PENDING
            )
        else:
            logger.info(f"🔄 Updating existing step: {step_name} (current status: {steps_dict[step_name].status.value})")
        
        step = steps_dict[step_name]
        
        # Handle step updates (all steps are independent, no sub-steps)
        if status == "in_progress":
            # Complete any other step that is currently in progress (only one step at a time)
            current_time = timestamp if isinstance(timestamp, (int, float)) else time.time()
            for other_step_name, other_step in steps_dict.items():
                if other_step_name != step_name and other_step.status == StepStatus.IN_PROGRESS:
                    logger.info(f"🔄 Auto-completing previous step: {other_step_name} (new step starting: {step_name})")
                    other_step.status = StepStatus.COMPLETED
                    other_step.end_time = current_time
                    if other_step.start_time:
                        other_step.duration = max(0.001, other_step.end_time - other_step.start_time)
                    else:
                        other_step.start_time = current_time - 0.001
                        other_step.duration = 0.001
            
            # Now start the new step
            if timestamp and isinstance(timestamp, (int, float)):
                step.status = StepStatus.IN_PROGRESS
                step.start_time = timestamp
                logger.info(f"▶️ Step started: {step_name} at {step.start_time}")
            else:
                step.start()
                logger.info(f"▶️ Step started: {step_name} (no timestamp)")
        elif status == "completed":
            completion_time = timestamp if isinstance(timestamp, (int, float)) else time.time()
            logger.info(f"✅ Step completing: {step_name} at {completion_time}")
            
            step.status = StepStatus.COMPLETED
            step.end_time = completion_time
            if step.start_time:
                step.duration = max(0.001, step.end_time - step.start_time)
            else:
                # If start_time is missing, set it just before end_time
                step.start_time = completion_time - 0.001
                step.duration = 0.001
            
            logger.info(f"✅ Step completed: {step_name} | duration={step.duration:.3f}s | start={step.start_time} | end={step.end_time}")
        elif status == "failed":
            if timestamp and isinstance(timestamp, (int, float)):
                step.status = StepStatus.FAILED
                step.end_time = timestamp
                if step.start_time:
                    step.duration = max(0.001, step.end_time - step.start_time)
            else:
                step.fail()
        
        # Calculate partial durations for in-progress steps (for real-time display)
        current_time = time.time()
        for step in steps_dict.values():
            # Calculate partial duration for in-progress steps
            if step.status == StepStatus.IN_PROGRESS:
                if step.start_time:
                    # Calculate duration from start_time to current time (real-time update)
                    step.duration = max(0.001, current_time - step.start_time)
                elif step.duration is None:
                    # If no start_time yet, set a minimal duration
                    step.duration = 0.001
            elif step.status == StepStatus.COMPLETED:
                # Ensure completed steps have duration calculated
                if step.start_time and step.end_time:
                    step.duration = max(0.001, step.end_time - step.start_time)
                elif step.start_time:
                    # If end_time is missing but start_time exists, use current time
                    if step.end_time is None:
                        step.end_time = current_time
                    step.duration = max(0.001, (step.end_time or current_time) - step.start_time)
                elif step.end_time:
                    # If only end_time exists, set a minimal duration
                    step.duration = 0.001
                else:
                    # No timing info at all, set minimal duration
                    if step.duration is None or step.duration <= 0:
                        step.duration = 0.001
        
        # Update Redis with current steps
        serialized_steps = []
        for step in steps_dict.values():
            step_dict = step.model_dump(mode='json')
            # Ensure duration is always present and valid
            if step_dict.get('duration') is None or step_dict.get('duration') <= 0:
                # Recalculate duration if missing or invalid
                if step_dict.get('start_time') and step_dict.get('end_time'):
                    step_dict['duration'] = max(0.001, step_dict['end_time'] - step_dict['start_time'])
                elif step_dict.get('start_time'):
                    step_dict['duration'] = max(0.001, time.time() - step_dict['start_time'])
                else:
                    step_dict['duration'] = 0.001
            serialized_steps.append(step_dict)
        
        redis_service.update_job(job_id, {
            "steps": serialized_steps,
            "updated_at": time.time()
        })
    
    try:
        # Job status and steps are already initialized above, just log start
        logger.info(f"Starting document processing: {job_id}")
        logger.info(f"🔍 step_callback is defined: {step_callback is not None}")
        
        # Process document using parser service with all options
        result = await document_parser.parse_document(
            file_path=file_path,
            output_format=options.output_format,
            force_ocr=options.force_ocr,
            extract_images=options.extract_images,
            paginate_output=options.paginate_output,
            language=options.language,
            step_callback=step_callback
        )
        
        # Convert to ProcessingResult for validation
        processing_result = ProcessingResult.from_marker_result(result)
        
        # Serialize to pure Python dict for Redis storage
        # Use mode='json' to ensure all nested objects are properly serialized
        redis_service.update_job(job_id, {
            "result": processing_result.model_dump(mode='json'),
            "updated_at": time.time()
        })
        
        # Save results
        redis_service.update_job(job_id, {
            "status": JobStatus.COMPLETED.value,
            "steps": [s.model_dump(mode='json') for s in steps_dict.values()],
            "updated_at": time.time()
        })
        
        logger.info(f"Document processing completed: {job_id}")
        
    except Exception as e:
        logger.error(f"Document processing failed for {job_id}: {str(e)}")
        
        # Mark all in-progress steps as failed
        for step in steps_dict.values():
            if step.status == StepStatus.IN_PROGRESS:
                step.fail()
        
        redis_service.update_job(job_id, {
            "status": JobStatus.FAILED.value,
            "error_message": str(e),
            "steps": [s.model_dump(mode='json') for s in steps_dict.values()],
            "updated_at": time.time()
        }) 