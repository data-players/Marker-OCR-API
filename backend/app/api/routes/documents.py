"""
Document processing endpoints for file upload and PDF conversion.
Main API routes for the document processing functionality.
"""

import uuid
import asyncio
from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
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
from app.models.enums import ProcessingOptions, OutputFormat
from app.services.file_handler import FileHandlerService
from app.services.document_parser import DocumentParserService
from app.utils.validators import validate_filename, validate_job_id
from app.api.dependencies import get_file_handler, get_document_parser

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Store for tracking job statuses
job_store = {}


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_handler: FileHandlerService = Depends(get_file_handler)
):
    """
    Upload a file to the server.
    Returns file ID for subsequent processing.
    """
    try:
        # Validate file
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
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/process", response_model=DocumentProcessResponse)
async def process_document(
    file_id: str = Form(...),
    processing_option: ProcessingOptions = Form(ProcessingOptions.ACCURATE),
    output_format: OutputFormat = Form(OutputFormat.BOTH),
    force_ocr: bool = Form(False),
    extract_images: bool = Form(True),
    extract_tables: bool = Form(True),
    language: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    file_handler: FileHandlerService = Depends(get_file_handler),
    document_parser: DocumentParserService = Depends(get_document_parser)
):
    """
    Process an uploaded document.
    Starts background processing and returns job ID for tracking.
    """
    logger.info(f"Document processing request: {file_id}")
    
    try:
        # Validate file exists
        file_path = await file_handler.get_file_path(file_id)
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create processing options object
        options = DocumentProcessRequest(
            processing_option=processing_option,
            output_format=output_format,
            force_ocr=force_ocr,
            extract_images=extract_images,
            extract_tables=extract_tables,
            language=language
        )
        
        # Store job status
        current_time = asyncio.get_event_loop().time()
        job_store[job_id] = {
            "status": JobStatus.PENDING,
            "file_id": file_id,
            "created_at": current_time,
            "updated_at": current_time,
            "progress": 0,
            "result": None,
            "error": None
        }
        
        # Start background processing
        background_tasks.add_task(
            process_document_background,
            job_id,
            str(file_path),
            options,
            document_parser,
            file_handler
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
async def get_job_status(job_id: str):
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
    
    if job_id not in job_store:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    job_data = job_store[job_id]
    
    return JobResponse(
        job_id=job_id,
        status=JobStatus(job_data["status"]),
        created_at=job_data["created_at"],
        updated_at=job_data["updated_at"],
        progress=job_data.get("progress"),
        result=job_data.get("result"),
        error_message=job_data.get("error_message")
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
    format: str = "json"
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
    
    if job_id not in job_store:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    job_data = job_store[job_id]
    
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
    options: ProcessingOptions,
    document_parser: DocumentParserService,
    file_handler: FileHandlerService
):
    """
    Background task for document processing.
    Updates job status and stores results.
    """
    try:
        # Update job status to processing
        job_store[job_id]["status"] = JobStatus.PROCESSING.value
        job_store[job_id]["progress"] = 10.0
        
        logger.info(f"Starting document processing: {job_id}")
        
        # Simulate processing steps with progress updates
        await asyncio.sleep(1)
        job_store[job_id]["progress"] = 30.0
        
        # Process document using parser service
        result = await document_parser.parse_document(
            file_path=file_path,
            processing_options=options.processing_option,
            output_format=options.output_format
        )
        
        # Convert to ProcessingResult for validation
        processing_result = ProcessingResult.from_marker_result(result)
        
        # Store the validated result
        job_store[job_id]["result"] = processing_result
        
        job_store[job_id]["progress"] = 90.0
        
        # Save results
        # In a real implementation, save to disk or database
        job_store[job_id]["status"] = JobStatus.COMPLETED.value
        job_store[job_id]["progress"] = 100.0
        
        logger.info(f"Document processing completed: {job_id}")
        
    except Exception as e:
        logger.error(f"Document processing failed for {job_id}: {str(e)}")
        
        job_store[job_id]["status"] = JobStatus.FAILED.value
        job_store[job_id]["error_message"] = str(e)
        job_store[job_id]["progress"] = 0.0 