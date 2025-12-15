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
    
    def create_step(name: str, description: str, sub_steps_list: Optional[List[str]] = None) -> ProcessingStep:
        """Create a new processing step with optional predefined sub-steps."""
        sub_steps_detailed = None
        if sub_steps_list:
            sub_steps_detailed = [
                SubStep(name=sub_name, status=StepStatus.PENDING)
                for sub_name in sub_steps_list
            ]
        
        step = ProcessingStep(
            name=name,
            description=description,
            status=StepStatus.PENDING,
            sub_steps_detailed=sub_steps_detailed
        )
        steps_dict[name] = step
        return step
    
    # Pre-create OCR Processing meta-step with sub-steps
    # Sub-steps will be updated by Marker wrappers (tqdm/log handlers)
    ocr_sub_steps = [
        "🔍 Recognizing document layout",
        "🔍 Running OCR error detection",
        "📦 Detecting bounding boxes",
        "📊 Recognizing tables",
        "📝 Extracting text",
        "📄 Processing pages",
        "🏗️ Building JSON structure",
        "🔍 Analyzing document structure",
    ]
    
    # Create OCR Processing meta-step with predefined sub-steps
    create_step(
        "📄 OCR Processing",
        "Processing document with OCR and structure analysis",
        sub_steps_list=ocr_sub_steps
    )
    
    # Initialize steps in Redis immediately so frontend can display them
    redis_service.update_job(job_id, {
        "status": JobStatus.PROCESSING.value,
        "steps": [s.model_dump(mode='json') for s in steps_dict.values()],
        "updated_at": time.time()
    })
    logger.info(f"Initialized {len(steps_dict)} processing steps in Redis for job {job_id}")
    
    def _group_small_substeps(step: ProcessingStep):
        """
        Group consecutive completed sub-steps with duration < 10ms into a single macro step.
        IMPORTANT: This function does NOT remove the original small steps - they remain visible.
        It only creates/updates a macro step that summarizes them for display purposes.
        All steps remain visible throughout processing.
        The macro step is only created/updated when there are completed small steps.
        """
        if not step.sub_steps_detailed:
            return
        
        SMALL_STEP_THRESHOLD = 0.01  # 10ms in seconds
        MACRO_STEP_NAME = "⚡ Initialization and quick operations"
        
        # Check if macro step already exists
        existing_macro = None
        small_completed_steps = []
        
        # Find macro step and collect small completed steps
        for sub_step in step.sub_steps_detailed:
            if sub_step.name == MACRO_STEP_NAME:
                existing_macro = sub_step
            elif (sub_step.status == StepStatus.COMPLETED and 
                  sub_step.duration is not None and 
                  sub_step.duration < SMALL_STEP_THRESHOLD):
                small_completed_steps.append(sub_step)
        
        # Only create/update macro if we have completed small steps
        if len(small_completed_steps) == 0:
            # No completed small steps yet - remove macro if it exists (shouldn't happen, but safety)
            if existing_macro:
                step.sub_steps_detailed.remove(existing_macro)
            return
        
        # Calculate total duration of small steps
        total_small_duration = sum(s.duration for s in small_completed_steps if s.duration is not None)
        
        # Find earliest start_time and latest end_time for small steps
        start_times = [s.start_time for s in small_completed_steps if s.start_time is not None]
        end_times = [s.end_time for s in small_completed_steps if s.end_time is not None]
        
        # If macro exists, include its timing in the calculation
        if existing_macro:
            if existing_macro.start_time:
                start_times.append(existing_macro.start_time)
            if existing_macro.end_time:
                end_times.append(existing_macro.end_time)
            # Add existing macro duration to total
            if existing_macro.duration:
                total_small_duration += existing_macro.duration
            
            # Update existing macro step
            existing_macro.start_time = min(start_times) if start_times else None
            existing_macro.end_time = max(end_times) if end_times else None
            existing_macro.duration = max(total_small_duration, 0.001)
            existing_macro.status = StepStatus.COMPLETED
        else:
            # Create new macro step (but keep all original steps)
            macro_start_time = min(start_times) if start_times else None
            macro_end_time = max(end_times) if end_times else None
            
            macro_step = SubStep(
                name=MACRO_STEP_NAME,
                status=StepStatus.COMPLETED,
                start_time=macro_start_time,
                end_time=macro_end_time,
                duration=max(total_small_duration, 0.001)
            )
            # Add macro step to the list (at the beginning for visibility)
            # But keep all original steps - don't remove them
            step.sub_steps_detailed.insert(0, macro_step)
        
        # Sort by start_time to maintain chronological order
        step.sub_steps_detailed = sorted(
            step.sub_steps_detailed,
            key=lambda s: s.start_time if s.start_time else float('inf')
        )
        
        # Also update legacy sub_steps list for backward compatibility
        if step.sub_steps:
            # Add macro step name if not already present
            if MACRO_STEP_NAME not in step.sub_steps:
                # Insert at the beginning to maintain chronological order
                step.sub_steps.insert(0, MACRO_STEP_NAME)
    
    async def step_callback(step_name: str, status: str, timestamp_or_substep: float = None):
        """Callback to update step status in Redis."""
        import time
        
        # Debug: Log all step callbacks
        logger.info(f"📢 Step callback: {step_name} | status={status} | timestamp={timestamp_or_substep}")
        
        # IMPORTANT: All Marker steps are displayed, regardless of options
        # Marker always executes table recognition (pagination only affects output formatting)
        # This ensures users see what Marker is actually doing
        
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
        
        # Handle sub-step updates with timing
        if status == "sub_step":
            # Check if this is a completion with explicit timestamp (tuple)
            if isinstance(timestamp_or_substep, tuple) and len(timestamp_or_substep) == 2:
                sub_step_name, end_timestamp = timestamp_or_substep
                # Complete the specified sub-step with explicit timestamp
                if step.sub_steps_detailed:
                    for existing_sub in step.sub_steps_detailed:
                        if existing_sub.name == sub_step_name:
                            if existing_sub.status == StepStatus.IN_PROGRESS:
                                # Only complete if it was in progress
                                existing_sub.status = StepStatus.COMPLETED
                                # Ensure end_timestamp is >= start_time to avoid negative duration
                                if existing_sub.start_time:
                                    if end_timestamp < existing_sub.start_time:
                                        # If end_timestamp is before start_time, adjust start_time
                                        existing_sub.start_time = end_timestamp - 0.001
                                    existing_sub.end_time = end_timestamp
                                    existing_sub.duration = max(0.001, end_timestamp - existing_sub.start_time)
                                else:
                                    # If start_time is missing, set it just before end_time
                                    existing_sub.start_time = end_timestamp - 0.001
                                    existing_sub.end_time = end_timestamp
                                    existing_sub.duration = 0.001
                            elif existing_sub.status == StepStatus.PENDING:
                                # If it was pending, start and complete it immediately
                                existing_sub.status = StepStatus.COMPLETED
                                existing_sub.start_time = end_timestamp - 0.001  # Very short duration
                                existing_sub.end_time = end_timestamp
                                existing_sub.duration = 0.001
                            elif existing_sub.status == StepStatus.COMPLETED:
                                # Already completed - just update timing if needed
                                if existing_sub.end_time is None or end_timestamp > existing_sub.end_time:
                                    if existing_sub.start_time and end_timestamp >= existing_sub.start_time:
                                        existing_sub.end_time = end_timestamp
                                        existing_sub.duration = max(0.001, end_timestamp - existing_sub.start_time)
                            break
                
                # Don't group immediately - wait until all small steps are completed
                # This ensures all steps remain visible throughout processing
            elif isinstance(timestamp_or_substep, str):
                    sub_step_name = timestamp_or_substep
                    
                    # Initialize sub_steps_detailed if not exists
                    if step.sub_steps_detailed is None:
                        step.sub_steps_detailed = []
                    
                    # Always complete the previous in-progress sub-step first
                    current_time = time.time()
                    completed_a_small_step = False
                    for existing_sub in step.sub_steps_detailed:
                        if existing_sub.status == StepStatus.IN_PROGRESS:
                            existing_sub.status = StepStatus.COMPLETED
                            existing_sub.end_time = current_time
                            if existing_sub.start_time:
                                # Ensure duration is always positive
                                if current_time >= existing_sub.start_time:
                                    existing_sub.duration = current_time - existing_sub.start_time
                                else:
                                    # If current_time is before start_time (shouldn't happen, but safety check)
                                    existing_sub.start_time = current_time - 0.001
                                    existing_sub.duration = 0.001
                            else:
                                # If start_time is missing, set it just before current_time
                                existing_sub.start_time = current_time - 0.001
                                existing_sub.duration = 0.001
                            
                            # Check if this completed step is small (< 10ms)
                            if existing_sub.duration is not None and existing_sub.duration < 0.01:
                                completed_a_small_step = True
                    
                    # Find existing sub-step or create new one
                    sub_step = None
                    for existing_sub in step.sub_steps_detailed:
                        if existing_sub.name == sub_step_name:
                            sub_step = existing_sub
                            break
                    
                    if sub_step is None:
                        # New sub-step: create it
                        sub_step = SubStep(
                            name=sub_step_name,
                            status=StepStatus.IN_PROGRESS,
                            start_time=current_time
                        )
                        step.sub_steps_detailed.append(sub_step)
                    else:
                        # Existing sub-step: mark as in progress if pending or completed
                        if sub_step.status in [StepStatus.PENDING, StepStatus.COMPLETED]:
                            sub_step.status = StepStatus.IN_PROGRESS
                            sub_step.start_time = current_time
                            # Reset end_time and duration if it was previously completed
                            sub_step.end_time = None
                            sub_step.duration = None
                    
                    step.current_sub_step = sub_step_name
                    
                    # Also update legacy sub_steps for backward compatibility
                    if step.sub_steps is None:
                        step.sub_steps = []
                    if sub_step_name not in step.sub_steps:
                        step.sub_steps.append(sub_step_name)
                    
                    # Don't group immediately - wait until all small steps are completed
                    # This ensures all steps remain visible throughout processing
                    
            elif status == "in_progress":
                if timestamp_or_substep and isinstance(timestamp_or_substep, (int, float)):
                    step.status = StepStatus.IN_PROGRESS
                    step.start_time = timestamp_or_substep
                    logger.info(f"▶️ Step started: {step_name} at {step.start_time}")
                else:
                    step.start()
                    logger.info(f"▶️ Step started: {step_name} (no timestamp)")
            elif status == "completed":
                # Complete all in-progress sub-steps first
                completion_time = timestamp_or_substep if isinstance(timestamp_or_substep, (int, float)) else time.time()
                logger.info(f"✅ Step completing: {step_name} at {completion_time}")
                
                if step.sub_steps_detailed:
                    for sub_step in step.sub_steps_detailed:
                        if sub_step.status == StepStatus.IN_PROGRESS:
                            sub_step.status = StepStatus.COMPLETED
                            # Ensure completion_time is >= start_time
                            if sub_step.start_time:
                                if completion_time < sub_step.start_time:
                                    # Adjust start_time to be just before completion_time
                                    sub_step.start_time = completion_time - 0.001
                                sub_step.end_time = completion_time
                                sub_step.duration = max(0.001, completion_time - sub_step.start_time)
                            else:
                                # If start_time is missing, set it just before completion_time
                                sub_step.start_time = completion_time - 0.001
                                sub_step.end_time = completion_time
                                sub_step.duration = 0.001
                
                # Calculate total duration as sum of sub-steps durations
                if step.sub_steps_detailed:
                    # Filter out invalid durations and ensure all are positive
                    valid_durations = []
                    for sub in step.sub_steps_detailed:
                        if sub.duration is not None:
                            # Ensure duration is positive, fix if negative
                            if sub.duration <= 0:
                                # Fix negative or zero duration
                                if sub.start_time and sub.end_time and sub.end_time > sub.start_time:
                                    sub.duration = sub.end_time - sub.start_time
                                else:
                                    sub.duration = 0.001  # Minimum duration
                            valid_durations.append(sub.duration)
                    total_sub_duration = sum(valid_durations) if valid_durations else 0.0
                    # Use sum of sub-steps as the main step duration
                    if timestamp_or_substep and isinstance(timestamp_or_substep, (int, float)):
                        step.status = StepStatus.COMPLETED
                        step.end_time = timestamp_or_substep
                        # Adjust start_time to make duration match sum of sub-steps
                        if step.start_time:
                            step.duration = total_sub_duration
                        else:
                            step.start_time = timestamp_or_substep - total_sub_duration
                            step.duration = total_sub_duration
                    else:
                        step.complete()
                        step.duration = total_sub_duration
                        if step.start_time:
                            step.end_time = step.start_time + total_sub_duration
                else:
                    # Fallback to normal calculation if no sub-steps (now all steps are main steps)
                    if timestamp_or_substep and isinstance(timestamp_or_substep, (int, float)):
                        step.status = StepStatus.COMPLETED
                        step.end_time = timestamp_or_substep
                        if step.start_time:
                            step.duration = max(0.001, step.end_time - step.start_time)
                        else:
                            # If start_time is missing, set it just before end_time
                            step.start_time = timestamp_or_substep - 0.001
                            step.duration = 0.001
                    else:
                        step.complete()
                        # Ensure duration is set even if start_time was missing
                        if step.duration is None or step.duration <= 0:
                            if step.start_time and step.end_time:
                                step.duration = max(0.001, step.end_time - step.start_time)
                            elif step.start_time:
                                # If end_time is missing, use current time
                                import time
                                step.end_time = time.time()
                                step.duration = max(0.001, step.end_time - step.start_time)
                            else:
                                step.duration = 0.001
                
                logger.info(f"✅ Step completed: {step_name} | duration={step.duration:.3f}s | start={step.start_time} | end={step.end_time}")
                step.current_sub_step = None  # Clear current sub-step
            elif status == "failed":
                if timestamp_or_substep and isinstance(timestamp_or_substep, (int, float)):
                    step.status = StepStatus.FAILED
                    step.end_time = timestamp_or_substep
                    if step.start_time:
                        step.duration = step.end_time - step.start_time
                else:
                    step.fail()
            
            # Don't group here - grouping happens only when all small steps are completed
            # This ensures all steps remain visible throughout processing
        
        # Calculate partial durations for in-progress steps (for real-time display)
        # This ensures durations are always up-to-date before saving to Redis
        current_time = time.time()
        for step in steps_dict.values():
            # Calculate partial duration for in-progress main steps (now all steps are main steps)
            if step.status == StepStatus.IN_PROGRESS:
                if step.start_time:
                    # Calculate duration from start_time to current time (real-time update)
                    step.duration = max(0.001, current_time - step.start_time)
                elif step.duration is None:
                    # If no start_time yet, set a minimal duration
                    step.duration = 0.001
            elif step.status == StepStatus.COMPLETED:
                # Ensure completed steps have duration calculated (recalculate to be sure)
                if step.start_time and step.end_time:
                    # Recalculate duration to ensure accuracy
                    calculated_duration = max(0.001, step.end_time - step.start_time)
                    if step.duration is None or step.duration <= 0:
                        step.duration = calculated_duration
                    # Always ensure duration matches end_time - start_time for completed steps
                    step.duration = calculated_duration
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
            
            # Legacy: Handle sub-steps if they exist (for backward compatibility)
            if step.sub_steps_detailed:
                for sub_step in step.sub_steps_detailed:
                    if sub_step.status == StepStatus.IN_PROGRESS and sub_step.start_time:
                        # Calculate partial duration for in-progress sub-step
                        partial_duration = current_time - sub_step.start_time
                        if partial_duration > 0:
                            sub_step.duration = partial_duration
                    elif sub_step.status == StepStatus.COMPLETED and sub_step.duration is None:
                        # Ensure completed sub-steps have duration calculated
                        if sub_step.start_time and sub_step.end_time:
                            sub_step.duration = max(0.001, sub_step.end_time - sub_step.start_time)
                        elif sub_step.start_time:
                            sub_step.end_time = current_time
                            sub_step.duration = max(0.001, current_time - sub_step.start_time)
        
        # Update Redis with current steps (always grouped consistently)
        # This update happens after every step_callback call, ensuring real-time updates via SSE
        # Serialize steps and ensure durations are included
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
        
        # Final grouping is already done in step_callback before each Redis update
        # But ensure all steps are grouped one final time before completion
        for step in steps_dict.values():
            if step.status == StepStatus.COMPLETED and step.sub_steps_detailed:
                _group_small_substeps(step)
        
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