"""
Extraction queue service for managing OCR processing jobs.
Ensures only one extraction runs at a time using Redis as a queue backend.
"""

import json
import asyncio
import time
from typing import Dict, Any, Optional
from app.core.logger import get_logger
import logging as std_logging

logger = get_logger(__name__)


class ExtractionQueueService:
    """Service for managing extraction job queue."""
    
    QUEUE_KEY = "extraction:queue"
    PROCESSING_KEY = "extraction:processing"
    LOCK_TIMEOUT = 3600  # 1 hour timeout for a job
    
    def __init__(self, redis_service):
        self.redis_client = redis_service.client  # Access the underlying redis client
    
    async def clear_stale_state(self):
        """
        Clear all stale queue state on startup.
        Called when the server starts to ensure no leftover locks
        from a previous crash block new job processing.
        """
        loop = asyncio.get_event_loop()
        
        # Clear processing lock
        await loop.run_in_executor(None, self.redis_client.delete, self.PROCESSING_KEY)
        
        # Clear any pending jobs in queue (they are stale after restart)
        await loop.run_in_executor(None, self.redis_client.delete, self.QUEUE_KEY)
        
        # Clean up any stale job data keys
        keys = await loop.run_in_executor(
            None, 
            lambda: self.redis_client.keys("extraction:job:*")
        )
        if keys:
            await loop.run_in_executor(None, self.redis_client.delete, *keys)
        
        logger.info("[QUEUE] Cleared all stale queue state on startup")
    
    async def enqueue_job(self, job_data: Dict[str, Any]) -> str:
        """
        Add a job to the extraction queue.
        
        Args:
            job_data: Job data including execution_id, flow_id, etc.
            
        Returns:
            Job ID
        """
        job_id = job_data.get("execution_id")
        
        # Store job data in Redis
        self.redis_client.setex(
            f"extraction:job:{job_id}",
            3600,
            json.dumps(job_data)
        )
        
        # Add to queue
        self.redis_client.rpush(self.QUEUE_KEY, job_id)
        
        logger.info(f"Job enqueued: {job_id}")
        return job_id
    
    async def get_next_job(self) -> Optional[Dict[str, Any]]:
        """
        Get the next job from the queue if no job is currently processing.
        
        Returns:
            Job data if available, None otherwise
        """
        # Run Redis operations in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        
        # Check if a job is currently processing
        current_job = await loop.run_in_executor(None, self.redis_client.get, self.PROCESSING_KEY)
        if current_job:
            logger.debug(f"Job already processing: {current_job}")
            return None
        
        # Get next job from queue
        job_id = await loop.run_in_executor(None, self.redis_client.lpop, self.QUEUE_KEY)
        if not job_id:
            return None
        
        # Decode if bytes
        if isinstance(job_id, bytes):
            job_id = job_id.decode('utf-8')
        
        # Get job data
        job_data_str = await loop.run_in_executor(
            None, 
            self.redis_client.get, 
            f"extraction:job:{job_id}"
        )
        if not job_data_str:
            logger.warning(f"Job data not found for {job_id}")
            return None
        
        if isinstance(job_data_str, bytes):
            job_data_str = job_data_str.decode('utf-8')
        
        job_data = json.loads(job_data_str)
        
        # Mark as processing
        await loop.run_in_executor(
            None,
            self.redis_client.setex,
            self.PROCESSING_KEY,
            self.LOCK_TIMEOUT,
            job_id
        )
        
        logger.info(f"Starting job: {job_id}")
        return job_data
    
    async def mark_job_complete(self, job_id: str, success: bool = True):
        """
        Mark a job as complete and remove processing lock.
        
        Args:
            job_id: Job ID
            success: Whether the job succeeded
        """
        loop = asyncio.get_event_loop()
        
        # Remove processing lock
        await loop.run_in_executor(None, self.redis_client.delete, self.PROCESSING_KEY)
        
        # Remove job data
        await loop.run_in_executor(None, self.redis_client.delete, f"extraction:job:{job_id}")
        
        status = "completed" if success else "failed"
        logger.info(f"Job {status}: {job_id}")
    
    async def get_queue_size(self) -> int:
        """Get number of jobs waiting in queue."""
        size = self.redis_client.llen(self.QUEUE_KEY)
        return size if size else 0
    
    async def is_processing(self) -> bool:
        """Check if a job is currently processing."""
        return self.redis_client.exists(self.PROCESSING_KEY) > 0
    
    async def get_processing_job(self) -> Optional[str]:
        """Get the ID of the job currently processing."""
        job_id = self.redis_client.get(self.PROCESSING_KEY)
        if isinstance(job_id, bytes):
            job_id = job_id.decode('utf-8')
        return job_id
