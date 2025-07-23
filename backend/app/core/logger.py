"""
Structured logging configuration using structlog.
Provides consistent logging across the application.
"""

import sys
import logging
from typing import Dict, Any
import structlog
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper())
    )
    
    # Configure processors based on format preference
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.set_exc_info,
        structlog.processors.StackInfoRenderer(),
    ]
    
    if settings.log_format.lower() == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger instance for the class."""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
    
    def log_operation(self, operation: str, **kwargs) -> None:
        """Log an operation with context."""
        self.logger.info(f"Operation: {operation}", **kwargs)
    
    def log_error(self, error: Exception, operation: str = None, **kwargs) -> None:
        """Log an error with context."""
        context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            **kwargs
        }
        if operation:
            context["operation"] = operation
        
        self.logger.error("Error occurred", **context)
    
    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """Log performance metrics."""
        self.logger.info(
            f"Performance: {operation}",
            duration_seconds=duration,
            **kwargs
        ) 