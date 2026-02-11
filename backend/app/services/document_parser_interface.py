"""
Abstract interface for document parsing services.
Defines the contract that both library-based and API-based implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from app.models.enums import OutputFormat


class DocumentParserInterface(ABC):
    """
    Abstract interface for document parsing services.
    
    This interface allows switching between:
    - Library mode: Uses Marker library locally (requires GPU/heavy dependencies)
    - API mode: Uses Datalab cloud API (lightweight, no local dependencies)
    """
    
    @abstractmethod
    async def initialize_models(self, progress_callback=None) -> bool:
        """
        Initialize the service (load models for library mode, validate API key for API mode).
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def parse_document(
        self, 
        file_path: str, 
        output_format: OutputFormat,
        force_ocr: bool = False,
        extract_images: bool = False,
        paginate_output: bool = False,
        language: Optional[str] = None,
        step_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Parse a document and extract content.
        
        Args:
            file_path: Path to the PDF file
            output_format: Output format (json or markdown)
            force_ocr: Force OCR even if text is extractable
            extract_images: Extract and include images in the output
            paginate_output: Add page separators in output
            language: Document language hint (ISO 639-1 code)
            step_callback: Optional callback for progress tracking
            
        Returns:
            Dictionary containing:
            - text: Content for LLM (markdown text or serialized JSON structure)
            - markdown_content: Raw markdown (only for markdown output, None for JSON)
            - rich_structure: Native JSON structure (only for JSON output, None for markdown)
            - metadata: Document metadata
            - images: Extracted images
            - processing_time: Time taken to process
        """
        pass
    
    @abstractmethod
    def get_model_status(self) -> Dict[str, Any]:
        """
        Get current service status.
        
        Returns:
            Dictionary with status information:
            - status: "ready", "loading", or "error"
            - message: Human-readable status message
            - models_loaded: Boolean indicating if ready to process
            - error: Error message if any
            - mode: "library" or "api"
        """
        pass
    
    @abstractmethod
    async def shutdown(self):
        """Clean up resources."""
        pass
