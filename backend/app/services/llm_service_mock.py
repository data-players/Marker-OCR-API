"""
Mock LLM service for testing without external API calls.
Simulates LLM analysis for fast unit tests.
"""

import json
import asyncio
from typing import Dict, Any, List, Union
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
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Simulate LLM analysis with mock data.
        Supports root type (object or array).
        
        Args:
            ocr_content: The text output from OCR processing
            introduction: User-provided introduction explaining the extraction task
            schema: JSON schema defining expected structure with type, properties/items
            
        Returns:
            Mock structured data matching the schema (dict or list based on root type)
        """
        logger.info("Mock LLM analysis started")
        
        # Simulate API delay
        await asyncio.sleep(0.5)
        
        # Generate mock result based on schema (supports root type)
        result = self._generate_mock_from_root_schema(schema, ocr_content)
        
        logger.info("Mock LLM analysis completed")
        return result
    
    def _generate_mock_from_root_schema(
        self,
        schema: Dict[str, Any],
        ocr_content: str
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Generate mock result based on root schema type.
        
        Args:
            schema: Root schema with type, properties/items
            ocr_content: OCR content (used for realistic mock data)
            
        Returns:
            Mock data (dict for object root, list for array root)
        """
        root_type = schema.get("type", "object")
        
        if root_type == "array":
            # Array root type
            items = schema.get("items", {})
            item_type = items.get("type", "object") if items else "object"
            
            if item_type == "object":
                item_properties = items.get("properties", {})
                if item_properties:
                    return [
                        self._generate_mock_result(item_properties, ocr_content),
                        self._generate_mock_result(item_properties, ocr_content)
                    ]
                return [{"mock_key": "mock_value_1"}, {"mock_key": "mock_value_2"}]
            else:
                # Array of primitives
                return self._generate_mock_primitive_array(item_type)
        else:
            # Object root type
            properties = schema.get("properties", {})
            if properties:
                return self._generate_mock_result(properties, ocr_content)
            return {"mock_key": "mock_value"}
    
    def _generate_mock_primitive_array(self, item_type: str) -> List[Any]:
        """Generate mock array of primitive types."""
        if item_type == "string":
            return ["mock_item_1", "mock_item_2"]
        elif item_type == "number":
            return [1.5, 2.5]
        elif item_type == "integer":
            return [1, 2]
        elif item_type == "boolean":
            return [True, False]
        else:
            return ["mock_item_1", "mock_item_2"]
    
    def _generate_mock_result(
        self,
        schema: Dict[str, Any],
        ocr_content: str,
        depth: int = 0
    ) -> Dict[str, Any]:
        """
        Generate mock result matching the schema (supports nested structures).
        
        Args:
            schema: Expected schema
            ocr_content: OCR content (used for realistic mock data)
            depth: Current nesting depth
            
        Returns:
            Mock data matching schema
        """
        if depth > 5:  # Limit recursion
            return {}
        
        result = {}
        
        for field_name, field_def in schema.items():
            field_type = field_def.get("type", "string")
            description = field_def.get("description", "")
            required = field_def.get("required", False)
            
            # Generate mock value based on type
            if field_type == "string":
                result[field_name] = f"Mock {field_name}"
            elif field_type in ["number"]:
                result[field_name] = 42.5
            elif field_type == "integer":
                result[field_name] = 42
            elif field_type == "boolean":
                result[field_name] = True
            elif field_type == "array":
                result[field_name] = self._generate_mock_array(field_def, depth)
            elif field_type == "object":
                result[field_name] = self._generate_mock_object(field_def, depth)
            elif not required:
                result[field_name] = None
            else:
                result[field_name] = "mock_value"
        
        return result
    
    def _generate_mock_object(
        self,
        field_def: Dict[str, Any],
        depth: int
    ) -> Dict[str, Any]:
        """
        Generate mock object with nested properties.
        
        Args:
            field_def: Field definition with properties
            depth: Current nesting depth
            
        Returns:
            Mock object matching schema
        """
        properties = field_def.get("properties", {})
        if properties:
            return self._generate_mock_result(properties, "", depth + 1)
        return {"mock_key": "mock_value"}
    
    def _generate_mock_array(
        self,
        field_def: Dict[str, Any],
        depth: int
    ) -> list:
        """
        Generate mock array with items matching schema.
        
        Args:
            field_def: Field definition with items
            depth: Current nesting depth
            
        Returns:
            Mock array with 2 items
        """
        items = field_def.get("items", {})
        if not items:
            return ["mock_item_1", "mock_item_2"]
        
        item_type = items.get("type", "string")
        
        if item_type == "object":
            # Array of objects
            item_properties = items.get("properties", {})
            if item_properties:
                return [
                    self._generate_mock_result(item_properties, "", depth + 1),
                    self._generate_mock_result(item_properties, "", depth + 1)
                ]
            return [{"mock_key": "mock_value_1"}, {"mock_key": "mock_value_2"}]
        
        elif item_type == "string":
            return ["mock_item_1", "mock_item_2"]
        elif item_type in ["number"]:
            return [1.5, 2.5]
        elif item_type == "integer":
            return [1, 2]
        elif item_type == "boolean":
            return [True, False]
        else:
            return ["mock_item_1", "mock_item_2"]
    
    async def shutdown(self):
        """Cleanup resources on service shutdown."""
        logger.info("Mock LLM service shutdown complete")
