"""
Configuration management using Pydantic Settings.
Centralized configuration for the entire application.
"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = Field(default="Marker OCR API", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment")
    
    # Server
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8000, description="Port to bind to")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    # File handling
    upload_dir: str = Field(default="./uploads", description="Upload directory")
    output_dir: str = Field(default="./outputs", description="Output directory")
    max_file_size: int = Field(default=50 * 1024 * 1024, description="Max file size in bytes")
    allowed_extensions: List[str] = Field(
        default=[".pdf"], 
        description="Allowed file extensions"
    )
    
    # Marker configuration
    marker_batch_size: int = Field(default=1, description="Marker processing batch size")
    marker_use_gpu: bool = Field(default=True, description="Use GPU for Marker processing")
    marker_force_ocr: bool = Field(default=False, description="Force OCR for all documents")
    
    # Redis (for background tasks)
    redis_url: str = Field(default="redis://redis:6379/0", description="Redis URL")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings() 