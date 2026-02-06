"""
Main FastAPI application with routing, middleware, and error handling.
Entry point for the Marker OCR API service.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exception_handlers import http_exception_handler
import time
import asyncio

from app.core.config import settings
from app.core.logger import setup_logging, get_logger
from app.core.exceptions import BaseAPIException
from app.core.database import init_db, close_db
from app.models.response_models import ErrorResponse
from app.api.routes import health, documents, llm_analysis, combined_analysis
from app.api.routes import auth, workspaces, flows, extract
from app.api.dependencies import cleanup_services, get_document_parser
from pydantic import ValidationError

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Global state for model loading
model_loading_state = {
    "status": "loading",  # loading, ready, error
    "progress": 0,
    "message": "Initializing...",
    "error": None,
    "models_loaded": False
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async context manager for application lifespan events.
    Handles startup and shutdown procedures.
    """
    # Startup
    logger.info("Starting Marker OCR API service")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Create necessary directories
    from pathlib import Path
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize database
    logger.info("Initializing database...")
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Database initialization failed: {str(e)}")
        # Continue startup - database may not be needed for all operations
    
    # Initialize Marker models at startup
    logger.info("Initializing Marker models...")
    model_loading_state["message"] = "Loading Marker AI models..."
    model_loading_state["progress"] = 10
    
    try:
        # Get document parser and initialize models
        document_parser = get_document_parser()
        await document_parser.initialize_models()
        
        model_loading_state["status"] = "ready"
        model_loading_state["progress"] = 100
        model_loading_state["message"] = "All models loaded successfully"
        model_loading_state["models_loaded"] = True
        model_loading_state["error"] = None
        
        logger.info("✅ All Marker models loaded successfully")
        
    except Exception as e:
        model_loading_state["status"] = "error"
        model_loading_state["progress"] = 0
        model_loading_state["message"] = f"Failed to load models: {str(e)}"
        model_loading_state["error"] = str(e)
        model_loading_state["models_loaded"] = False
        
        logger.error(f"❌ Failed to load Marker models: {str(e)}")
        # Continue startup even if models fail to load - they can be loaded later
    
    try:
        yield
    except asyncio.CancelledError:
        # Lifespan was cancelled (e.g., during hot reload)
        # This is normal behavior - log at debug level and re-raise
        logger.debug("Lifespan cancelled during hot reload")
        raise
    
    # Shutdown
    logger.info("Shutting down Marker OCR API service")
    try:
        await cleanup_services()
        await close_db()
    except asyncio.CancelledError:
        # Cleanup was cancelled - this is normal during hot reload
        logger.debug("Cleanup cancelled during hot reload")
        raise
    except Exception as e:
        # Log other cleanup errors but don't fail shutdown
        logger.warning(f"Error during cleanup: {str(e)}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    ## Marker OCR API
    
    A high-performance API for converting PDF documents to structured JSON and Markdown format 
    using the Marker library. Features include:
    
    * **PDF Upload**: Secure file upload with validation
    * **Document Processing**: Convert PDFs to JSON/Markdown with configurable options
    * **Background Processing**: Asynchronous processing with job tracking
    * **Multiple Output Formats**: JSON or Markdown
    * **Processing Options**: Fast, accurate, or OCR-only modes
    * **Health Monitoring**: Comprehensive health checks and metrics
    
    ### Authentication
    
    If an API key is configured, include it in the `X-API-Key` header.
    
    ### Rate Limits
    
    API requests are rate limited to ensure fair usage.
    """,
    version=settings.version,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "0.0.0.0", "127.0.0.1", "api.ocr.data-players.com", "marker-ocr-backend"]
    )


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    
    # Add request ID to context
    request_id = request.headers.get("X-Request-ID", f"req_{int(start_time)}")
    
    try:
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        # Log request completion
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
            request_id=request_id
        )
        
        return response
    
    except asyncio.CancelledError:
        # Request was cancelled (e.g., during hot reload)
        # This is normal behavior and should not be logged as an error
        # Don't re-raise to avoid 500 error - let it propagate naturally
        logger.debug(
            "Request cancelled",
            method=request.method,
            url=str(request.url),
            request_id=request_id
        )
        # Re-raise CancelledError - it's expected during hot reload
        # The exception handler will catch it and handle it gracefully
        raise
    
    except Exception as e:
        # Log unexpected errors but don't break the request flow
        process_time = time.time() - start_time
        logger.error(
            "Unexpected error in middleware",
            method=request.method,
            url=str(request.url),
            request_id=request_id,
            process_time=process_time,
            error=str(e)
        )
        raise  # Re-raise to let FastAPI handle it


# Custom exception handlers
@app.exception_handler(BaseAPIException)
async def custom_exception_handler(request: Request, exc: BaseAPIException):
    """Handle custom API exceptions with structured logging."""
    logger.error(
        "API exception occurred",
        error_type=type(exc).__name__,
        error_message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        url=str(request.url),
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.message,
            status_code=exc.status_code,
            details=exc.details
        ).model_dump(mode='json')
    )


@app.exception_handler(HTTPException)
async def http_exception_handler_custom(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured logging."""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url),
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=str(exc.detail),
            status_code=exc.status_code
        ).model_dump(mode='json')
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    logger.warning(
        "Validation error occurred",
        error_details=exc.errors(),
        url=str(request.url),
        method=request.method
    )
    
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=f"Validation error: {str(exc)}",
            status_code=400
        ).model_dump(mode='json')
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    # Skip CancelledError - it's handled separately
    if isinstance(exc, asyncio.CancelledError):
        raise
    
    logger.error(
        "Unexpected error occurred",
        error_type=type(exc).__name__,
        error_message=str(exc),
        url=str(request.url),
        method=request.method,
        exc_info=True
    )
    
    # Don't expose internal errors in production
    error_message = "Internal server error"
    if settings.debug:
        error_message = f"Internal server error: {str(exc)}"
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=error_message,
            status_code=500
        ).model_dump(mode='json')
    )


# Include routers
# Note: Tags are already defined in each router, no need to add them here
app.include_router(
    health.router,
    prefix="/api/v1"
)

app.include_router(
    documents.router,
    prefix="/api/v1"
)

app.include_router(
    llm_analysis.router,
    prefix="/api/v1"
)

app.include_router(
    combined_analysis.router,
    prefix="/api/v1"
)

# New routes: Authentication, Workspaces, Flows
app.include_router(
    auth.router,
    prefix="/api/v1"
)

app.include_router(
    workspaces.router,
    prefix="/api/v1"
)

app.include_router(
    flows.router,
    prefix="/api/v1"
)

app.include_router(
    extract.router,
    prefix="/api/v1"
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic service information."""
    return {
        "message": "Welcome to Marker OCR API",
        "version": settings.version,
        "docs_url": "/docs",
        "health_check": "/api/v1/health",
        "environment": settings.environment
    }


# Redirect /api to documentation
@app.get("/api")
async def api_redirect():
    """Redirect /api to the interactive API documentation."""
    return RedirectResponse(url="/docs")


# Additional endpoints for API information
@app.get("/api/v1/info")
async def api_info():
    """Get API information and capabilities."""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "features": {
            "pdf_processing": True,
            "background_jobs": True,
            "multiple_formats": True,
            "batch_processing": False  # Not implemented in this version
        },
        "limits": {
            "max_file_size_mb": settings.max_file_size // (1024 * 1024),
            "allowed_extensions": settings.allowed_extensions,
            "processing_timeout_seconds": 300
        },
        "endpoints": {
            "upload": "/api/v1/documents/upload",
            "process": "/api/v1/documents/process",
            "job_status": "/api/v1/documents/jobs/{job_id}",
            "download": "/api/v1/documents/download/{job_id}",
            "health": "/api/v1/health",
            "metrics": "/api/v1/metrics"
        }
    }


if __name__ == "__main__":
    # Use Hypercorn for HTTP/2 support in production, uvicorn for development
    if settings.environment == "production":
        import hypercorn.asyncio
        from hypercorn.config import Config
        
        config = Config()
        config.bind = [f"{settings.host}:{settings.port}"]
        config.loglevel = settings.log_level.lower()
        
        hypercorn.asyncio.serve(app, config)
    else:
        import uvicorn
        
        uvicorn.run(
            "app.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            log_level=settings.log_level.lower()
        ) 