"""
Redis service for job storage and caching.
Handles persistent storage of job statuses across container restarts.
"""

import json
import redis
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class RedisService:
    """Service for Redis operations, mainly for job storage."""
    
    def __init__(self):
        """Initialize Redis connection."""
        try:
            self.client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    def store_job(self, job_id: str, job_data: Dict[str, Any], ttl: int = 86400) -> bool:
        """
        Store job data in Redis with TTL.
        
        Args:
            job_id: Unique job identifier
            job_data: Job data dictionary
            ttl: Time to live in seconds (default 24 hours)
            
        Returns:
            True if stored successfully
        """
        try:
            key = f"job:{job_id}"
            value = json.dumps(job_data)
            self.client.setex(key, ttl, value)
            logger.debug(f"Stored job {job_id} in Redis")
            return True
        except Exception as e:
            logger.error(f"Failed to store job {job_id}: {str(e)}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job data from Redis.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Job data dictionary or None if not found
        """
        try:
            key = f"job:{job_id}"
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {str(e)}")
            return None
    
    def update_job(self, job_id: str, updates: Dict[str, Any], ttl: int = 86400) -> bool:
        """
        Update job data in Redis.
        
        Args:
            job_id: Unique job identifier
            updates: Dictionary of fields to update
            ttl: Time to live in seconds (default 24 hours)
            
        Returns:
            True if updated successfully
        """
        try:
            existing_data = self.get_job(job_id)
            if existing_data is None:
                logger.warning(f"Job {job_id} not found for update")
                return False
            
            # Merge updates
            existing_data.update(updates)
            return self.store_job(job_id, existing_data, ttl)
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {str(e)}")
            return False
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete job data from Redis.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            key = f"job:{job_id}"
            self.client.delete(key)
            logger.debug(f"Deleted job {job_id} from Redis")
            return True
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {str(e)}")
            return False
    
    def list_jobs(self, pattern: str = "job:*") -> list:
        """
        List all job IDs matching pattern.
        
        Args:
            pattern: Redis key pattern
            
        Returns:
            List of job IDs
        """
        try:
            keys = self.client.keys(pattern)
            # Extract job IDs from keys
            job_ids = [key.replace("job:", "") for key in keys]
            return job_ids
        except Exception as e:
            logger.error(f"Failed to list jobs: {str(e)}")
            return []
    
    def ping(self) -> bool:
        """
        Check if Redis is accessible.
        
        Returns:
            True if Redis is accessible
        """
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {str(e)}")
            return False

