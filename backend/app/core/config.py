"""
Configuration management using Pydantic Settings.
Centralized configuration for the entire application.
"""

from typing import Optional, List
from pydantic import Field, ConfigDict
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
        default=["*"],
        description="Allowed CORS origins (use ['*'] for all origins or specify list)"
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
    
    # Security
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    
    # LLM Configuration (Infomaniak API)
    llm_product_id: str = Field(
        default="",
        description="Infomaniak product ID for AI API"
    )
    llm_api_token: str = Field(
        default="",
        description="Infomaniak API Bearer token for authentication"
    )
    llm_model: str = Field(
        default="mistral3",
        description="LLM model to use (e.g., mistral3, gpt-3.5-turbo, gpt-4)"
    )
    llm_timeout: int = Field(
        default=60,
        description="LLM API timeout in seconds"
    )
    
    @property
    def llm_api_url(self) -> str:
        """Construct the full Infomaniak API URL with product_id."""
        if not self.llm_product_id:
            return ""
        return f"https://api.infomaniak.com/1/ai/{self.llm_product_id}/openai/chat/completions"
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings() 