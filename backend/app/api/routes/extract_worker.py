"""
Background worker for processing extraction jobs from the queue.
Ensures only one Marker OCR analysis runs at a time.
"""

import asyncio
import time
from typing import Optional
from app.core.logger import get_logger
from app.core.database import get_async_session_maker
from app.models.enums import OutputFormat
from app.services.flow_service import FlowService

logger = get_logger(__name__)


async def extraction_worker(
    file_handler,
    document_parser,
    llm_service,
    redis_service,
    extraction_queue
):
    """
    Worker that processes extraction jobs from the queue one at a time.
    Runs indefinitely, polling for new jobs.
    """
    logger.info("[WORKER] Extraction worker initialized, clearing stale state...")
    
    # Clear any stale locks/jobs from a previous server run
    await extraction_queue.clear_stale_state()
    
    logger.info("[WORKER] Starting main loop...")
    
    loop_count = 0
    while True:
        try:
            loop_count += 1
            if loop_count % 10 == 0:
                logger.debug(f"[WORKER] Loop iteration {loop_count}, polling for jobs...")
            
            # Try to get next job
            job_data = await extraction_queue.get_next_job()
            
            if not job_data:
                # No job ready, sleep and retry
                if loop_count % 20 == 0:
                    logger.debug("[WORKER] No job in queue, sleeping...")
                await asyncio.sleep(0.5)  # Reduced sleep time for faster response
                continue
            
            execution_id = job_data.get("execution_id")
            logger.info(f"[WORKER] Got job from queue: {execution_id}")
            
            success = False
            try:
                await process_queued_extraction(
                    job_data=job_data,
                    file_handler=file_handler,
                    document_parser=document_parser,
                    llm_service=llm_service,
                    redis_service=redis_service
                )
                success = True
                logger.info(f"[WORKER] Completed job {execution_id}")
                
            except Exception as e:
                logger.error(f"[WORKER] Failed job {execution_id}: {str(e)}", exc_info=True)
            
            finally:
                # ALWAYS release the lock, even on crash
                try:
                    await extraction_queue.mark_job_complete(execution_id, success=success)
                except Exception as lock_err:
                    logger.error(f"[WORKER] Failed to release lock for {execution_id}: {lock_err}")
        
        except asyncio.CancelledError:
            logger.info("Extraction worker stopped")
            break
        
        except Exception as e:
            logger.error(f"Unexpected error in extraction worker: {str(e)}", exc_info=True)
            await asyncio.sleep(1)  # Avoid rapid loops on errors


async def process_queued_extraction(
    job_data: dict,
    file_handler,
    document_parser,
    llm_service,
    redis_service
):
    """
    Process a single extraction job from the queue.
    """
    execution_id = job_data.get("execution_id")
    flow_id = job_data.get("flow_id")
    document_url = job_data.get("document_url")
    file_content_hex = job_data.get("file_content")
    file_name = job_data.get("file_name")
    extraction_schema = job_data.get("extraction_schema")
    introduction = job_data.get("introduction")
    ocr_options = job_data.get("ocr_options", {})
    
    logger.info(f"[PROCESS] Starting process_queued_extraction for {execution_id}")
    logger.info(f"[PROCESS] Document URL: {document_url}, File: {file_name}")
    
    # Convert hex back to bytes if present
    file_content = None
    if file_content_hex:
        file_content = bytes.fromhex(file_content_hex)
    
    logger.info(f"[PROCESS] Opening DB session for {execution_id}")
    async with get_async_session_maker()() as db:
        flow_service = FlowService(db)
        
        try:
            # Initialize Redis
            logger.info(f"[PROCESS] Initializing Redis for {execution_id}")
            redis_service.store_execution(execution_id, {"steps": [], "current_step": None})
            
            # Get file
            logger.info(f"[PROCESS] Getting file for {execution_id}")
            if document_url:
                logger.info(f"[PROCESS] Downloading from URL: {document_url}")
                file_info = await file_handler.download_file_from_url(document_url)
                file_id = file_info["file_id"]
                logger.info(f"[PROCESS] Downloaded file {file_id}")
            elif file_content and file_name:
                logger.info(f"[PROCESS] Saving uploaded file: {file_name}")
                file_info = await file_handler.save_uploaded_file(file_content, file_name)
                file_id = file_info["file_id"]
                logger.info(f"[PROCESS] Saved file {file_id}")
            else:
                raise ValueError("Neither document_url nor file_content provided")
            
            # Update status to processing
            logger.info(f"[PROCESS] Getting execution from DB: {execution_id}")
            execution = await flow_service.get_execution(execution_id)
            if execution:
                await flow_service.update_execution(execution, status="processing")
                await db.commit()  # Commit so other sessions see the status change
                logger.info(f"[PROCESS] Status updated to processing: {execution_id}")
            else:
                logger.error(f"[PROCESS] Execution not found in DB: {execution_id}")
            
            # Get file path
            logger.info(f"[PROCESS] Getting file path for {file_id}")
            file_path = await file_handler.get_file_path(file_id)
            logger.info(f"[PROCESS] File path: {file_path}")
            
            # OCR Processing - respect user's format choice (JSON or Markdown)
            # JSON mode: LLM receives serialized Marker JSON structure
            # Markdown mode: LLM receives raw Marker markdown
            start_time = time.time()
            output_format = OutputFormat(ocr_options.get("output_format", "markdown"))
            force_ocr = ocr_options.get("force_ocr", False)
            
            logger.info(f"[PROCESS] Starting OCR for execution {execution_id}, format={output_format.value}")
            result = await document_parser.parse_document(
                file_path=str(file_path),
                output_format=output_format,
                force_ocr=force_ocr,
                step_callback=None
            )
            logger.info(f"[PROCESS] OCR completed for {execution_id}")
            
            ocr_content = result.get("text") or result.get("markdown_content") or ""
            logger.info(f"[PROCESS] OCR content length: {len(ocr_content)}")
            
            if not ocr_content:
                logger.warning(f"[PROCESS] Empty OCR content for {execution_id}")
            
            # LLM Analysis
            logger.info(f"[PROCESS] Starting LLM analysis for execution {execution_id}")
            extracted_data = await llm_service.analyze_ocr_content(
                ocr_content=ocr_content,
                introduction=introduction or "",
                schema=extraction_schema
            )
            logger.info(f"[PROCESS] LLM analysis completed for {execution_id}")
            
            # Update with results
            processing_time = time.time() - start_time
            logger.info(f"[PROCESS] Updating execution with results: {execution_id}")
            
            # Refresh execution from DB (may have been modified by commit)
            db.expire_all()
            execution = await flow_service.get_execution(execution_id)
            if execution:
                await flow_service.update_execution(
                    execution=execution,
                    status="completed",
                    extracted_data=extracted_data,
                    processing_time=processing_time
                )
                await db.commit()  # Commit so /sync and /status see "completed"
                logger.info(f"[PROCESS] Execution updated to completed: {execution_id}")
            else:
                logger.error(f"[PROCESS] Execution not found for update: {execution_id}")
            
            # Update Redis
            redis_service.update_execution(execution_id, {
                "status": "completed",
                "processing_time": processing_time
            })
            
            logger.info(f"[PROCESS] Extraction completed for {execution_id} in {processing_time:.2f}s")
        
        except Exception as e:
            logger.error(f"Extraction failed for {execution_id}: {str(e)}", exc_info=True)
            
            try:
                db.expire_all()
                execution = await flow_service.get_execution(execution_id)
                if execution:
                    await flow_service.update_execution(
                        execution=execution,
                        status="failed",
                        error_message=str(e)
                    )
                    await db.commit()  # Commit failure status
            except Exception as db_error:
                logger.error(f"Failed to update status: {str(db_error)}")
            
            try:
                redis_service.update_execution(execution_id, {
                    "status": "failed",
                    "error_message": str(e)
                })
            except Exception as redis_error:
                logger.error(f"Failed to update Redis: {str(redis_error)}")
