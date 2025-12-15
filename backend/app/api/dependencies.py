"""
Dependency injection setup for FastAPI.
Provides singleton instances of services for request handling.
"""

from functools import lru_cache
from typing import Optional
from fastapi import Depends, HTTPException, Header

from app.core.config import settings
from app.services.file_handler import FileHandlerService
from app.services.document_parser import DocumentParserService
from app.services.redis_service import RedisService


# Service instances (singletons)
_file_handler_instance: Optional[FileHandlerService] = None
_document_parser_instance: Optional[DocumentParserService] = None
_redis_instance: Optional[RedisService] = None


@lru_cache()
def get_file_handler() -> FileHandlerService:
    """
    Get singleton instance of FileHandlerService.
    Uses LRU cache to ensure single instance across requests.
    """
    global _file_handler_instance
    
    if _file_handler_instance is None:
        _file_handler_instance = FileHandlerService()
    
    return _file_handler_instance


@lru_cache()
def get_document_parser() -> DocumentParserService:
    """
    Get singleton instance of DocumentParserService.
    Uses LRU cache to ensure single instance across requests.
    """
    global _document_parser_instance
    
    if _document_parser_instance is None:
        _document_parser_instance = DocumentParserService()
    
    return _document_parser_instance


@lru_cache()
def get_redis() -> RedisService:
    """
    Get singleton instance of RedisService.
    Uses LRU cache to ensure single instance across requests.
    """
    global _redis_instance
    
    if _redis_instance is None:
        _redis_instance = RedisService()
    
    return _redis_instance




def get_pagination_params(
    page: int = 1,
    per_page: int = 20
) -> dict:
    """
    Get validated pagination parameters.
    
    Args:
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Dictionary with validated pagination parameters
    """
    # Ensure reasonable limits
    page = max(1, page)
    per_page = max(1, min(per_page, 100))  # Cap at 100
    
    return {
        "page": page,
        "per_page": per_page,
        "offset": (page - 1) * per_page
    }


async def check_service_health() -> bool:
    """
    Check if core services are healthy.
    Can be used as a dependency for critical endpoints.
    
    Returns:
        True if services are healthy
        
    Raises:
        HTTPException: If services are unhealthy
    """
    try:
        # Check file handler
        file_handler = get_file_handler()
        # Basic health check - ensure directories exist
        if not file_handler.upload_dir.exists() or not file_handler.output_dir.exists():
            raise HTTPException(
                status_code=503,
                detail="File system not accessible"
            )
        
        # Check document parser
        document_parser = get_document_parser()
        # In a real implementation, we might check if models are loaded
        
        return True
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )


class CommonDependencies:
    """
    Class-based dependencies for more complex scenarios.
    Useful for endpoints that need multiple services.
    """
    
    def __init__(
        self,
        file_handler: FileHandlerService = Depends(get_file_handler),
        document_parser: DocumentParserService = Depends(get_document_parser),
        pagination: dict = Depends(get_pagination_params),
        service_health: bool = Depends(check_service_health)
    ):
        self.file_handler = file_handler
        self.document_parser = document_parser
        self.pagination = pagination
        self.service_health = service_health


# Rate limiting dependency (placeholder)
async def rate_limit_check(
    x_forwarded_for: Optional[str] = Header(None)
) -> bool:
    """
    Rate limiting check (placeholder implementation).
    
    In a production system, this would:
    - Check Redis for request counts per IP/user
    - Implement sliding window or token bucket algorithms
    - Return 429 Too Many Requests if limit exceeded
    
    Args:
        x_forwarded_for: Client IP from proxy header
        
    Returns:
        True if request is within rate limits
    """
    # For now, always allow requests
    # In production, implement actual rate limiting logic
    return True


# Request ID dependency for tracing
async def get_request_id(
    x_request_id: Optional[str] = Header(None)
) -> str:
    """
    Get or generate request ID for tracing.
    
    Args:
        x_request_id: Request ID from header
        
    Returns:
        Request ID string
    """
    if x_request_id:
        return x_request_id
    
    # Generate new request ID if not provided
    import uuid
    return str(uuid.uuid4())


# Cleanup function for services
async def cleanup_services():
    """
    Cleanup function to be called on application shutdown.
    Ensures proper resource cleanup for all services.
    """
    global _file_handler_instance, _document_parser_instance
    
    try:
        if _document_parser_instance:
            await _document_parser_instance.shutdown()
            _document_parser_instance = None
        
        # File handler doesn't need async cleanup, but we reset the instance
        _file_handler_instance = None
        
    except Exception as e:
        # Log error but don't raise - shutdown should continue
        from app.core.logger import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error during service cleanup: {str(e)}") 