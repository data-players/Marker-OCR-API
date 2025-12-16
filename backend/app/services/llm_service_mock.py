"""
Mock LLM service for testing without external API calls.
Simulates LLM analysis for fast unit tests.
"""

import json
import asyncio
from typing import Dict, Any
from app.core.logger import get_logger

logger = get_logger(__name__)


class LLMServiceMock:
    """Mock LLM service that simulates extraction without external API calls."""
    
    def __init__(self):
        """Initialize mock LLM service."""
        logger.info("Initialized mock LLM service")
    
    async def analyze_ocr_content(
        self,
        ocr_content: str,
        introduction: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulate LLM analysis with mock data.
        
        Args:
            ocr_content: The text output from OCR processing
            introduction: User-provided introduction explaining the extraction task
            schema: JSON schema defining expected structure
            
        Returns:
            Dictionary containing mock structured data matching the schema
        """
        logger.info("Mock LLM analysis started")
        
        # Simulate API delay
        await asyncio.sleep(0.5)
        
        # Generate mock result based on schema
        result = self._generate_mock_result(schema, ocr_content)
        
        logger.info("Mock LLM analysis completed")
        return result
    
    def _generate_mock_result(
        self,
        schema: Dict[str, Any],
        ocr_content: str
    ) -> Dict[str, Any]:
        """
        Generate mock result matching the schema.
        
        Args:
            schema: Expected schema
            ocr_content: OCR content (used for realistic mock data)
            
        Returns:
            Mock data matching schema
        """
        result = {}
        
        for field_name, field_def in schema.items():
            field_type = field_def.get("type", "string")
            description = field_def.get("description", "")
            required = field_def.get("required", False)
            
            # Generate mock value based on type
            if field_type == "string":
                result[field_name] = f"Mock {field_name}: {description[:30]}"
            elif field_type in ["number", "integer"]:
                result[field_name] = 42
            elif field_type == "boolean":
                result[field_name] = True
            elif field_type == "array":
                result[field_name] = ["mock_item_1", "mock_item_2"]
            elif field_type == "object":
                result[field_name] = {"mock_key": "mock_value"}
            elif not required:
                result[field_name] = None
            else:
                result[field_name] = "mock_value"
        
        return result
    
    async def shutdown(self):
        """Cleanup resources on service shutdown."""
        logger.info("Mock LLM service shutdown complete")

