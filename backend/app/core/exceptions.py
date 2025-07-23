"""
Custom exceptions for structured error handling.
Each exception type maps to specific HTTP status codes.
"""

from typing import Optional, Dict, Any


class BaseAPIException(Exception):
    """Base exception for all API-related errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseAPIException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class FileNotFoundError(BaseAPIException):
    """Raised when a requested file is not found."""
    
    def __init__(self, filename: str, details: Optional[Dict[str, Any]] = None):
        message = f"File not found: {filename}"
        super().__init__(message, status_code=404, details=details)


class FileProcessingError(BaseAPIException):
    """Raised when file processing fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)


class UnsupportedFileTypeError(BaseAPIException):
    """Raised when an unsupported file type is uploaded."""
    
    def __init__(self, filename: str, allowed_types: list, details: Optional[Dict[str, Any]] = None):
        message = f"Unsupported file type for {filename}. Allowed types: {', '.join(allowed_types)}"
        super().__init__(message, status_code=415, details=details)


class FileSizeExceededError(BaseAPIException):
    """Raised when uploaded file exceeds size limit."""
    
    def __init__(self, size: int, max_size: int, details: Optional[Dict[str, Any]] = None):
        message = f"File size {size} bytes exceeds maximum allowed size {max_size} bytes"
        super().__init__(message, status_code=413, details=details)


class MarkerProcessingError(BaseAPIException):
    """Raised when Marker library processing fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Marker processing failed: {message}", status_code=500, details=details)


class AuthenticationError(BaseAPIException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class RateLimitError(BaseAPIException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=429, details=details) 