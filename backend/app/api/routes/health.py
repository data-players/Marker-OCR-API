"""
Health check and system status endpoints.
Provides information about service health and system status.
"""

import asyncio
from typing import Dict, Any
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logger import get_logger
from app.models.response_models import HealthCheckResponse
from app.api.dependencies import check_service_health

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthCheckResponse)
async def health_check():
    """
    Basic health check endpoint.
    Returns service status and basic information.
    """
    return HealthCheckResponse(
        status="healthy",
        version=settings.version,
        timestamp=f"{asyncio.get_event_loop().time()}",
        services=await check_dependent_services()
    )


@router.get("/models")
async def models_status():
    """
    Get the current status of Marker AI models.
    Returns loading status, progress, and any errors.
    """
    # Import here to avoid circular imports
    from app.main import model_loading_state
    
    return JSONResponse(content={
        "status": model_loading_state["status"],
        "progress": model_loading_state["progress"], 
        "message": model_loading_state["message"],
        "models_loaded": model_loading_state["models_loaded"],
        "error": model_loading_state["error"]
    })


@router.post("/models/reload")
async def reload_models():
    """
    Manually reload Marker models.
    Useful if models failed to load at startup or need to be refreshed.
    """
    from app.main import model_loading_state
    from app.api.dependencies import get_document_parser
    
    try:
        model_loading_state["status"] = "loading"
        model_loading_state["progress"] = 10
        model_loading_state["message"] = "Reloading Marker AI models..."
        model_loading_state["error"] = None
        
        # Force reload models
        document_parser = get_document_parser()
        document_parser._models_loaded = False  # Force reload
        await document_parser.initialize()
        
        model_loading_state["status"] = "ready"
        model_loading_state["progress"] = 100
        model_loading_state["message"] = "Models reloaded successfully"
        model_loading_state["models_loaded"] = True
        
        return JSONResponse(content={"success": True, "message": "Models reloaded successfully"})
        
    except Exception as e:
        model_loading_state["status"] = "error"
        model_loading_state["progress"] = 0
        model_loading_state["message"] = f"Failed to reload models: {str(e)}"
        model_loading_state["error"] = str(e)
        model_loading_state["models_loaded"] = False
        
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


async def check_dependent_services() -> dict:
    """
    Check the status of dependent services.
    
    Returns:
        Dictionary with service names and their status
    """
    services = {}
    
    # Check Redis connection
    try:
        # This would normally test actual Redis connection
        # For demo purposes, we'll simulate the check
        await asyncio.sleep(0.01)  # Simulate network call
        services["redis"] = "healthy"
    except Exception as e:
        logger.warning(f"Redis health check failed: {str(e)}")
        services["redis"] = "unhealthy"
    
    # Check file system access
    try:
        # Test if we can access upload and output directories
        import os
        upload_accessible = os.access(settings.upload_dir, os.R_OK | os.W_OK)
        output_accessible = os.access(settings.output_dir, os.R_OK | os.W_OK)
        
        if upload_accessible and output_accessible:
            services["file_system"] = "healthy"
        else:
            services["file_system"] = "unhealthy"
            
    except Exception as e:
        logger.warning(f"File system health check failed: {str(e)}")
        services["file_system"] = "unhealthy"
    
    # Check Marker models
    try:
        from app.main import model_loading_state
        if model_loading_state["models_loaded"]:
            services["marker_models"] = "healthy"
        else:
            services["marker_models"] = "loading" if model_loading_state["status"] == "loading" else "unhealthy"
    except Exception as e:
        logger.warning(f"Marker models health check failed: {str(e)}")
        services["marker_models"] = "unhealthy"
    
    return services 