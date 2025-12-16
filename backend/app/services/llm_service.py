"""
LLM service for post-OCR analysis with external LLM API (Infomaniak).
Handles prompt generation and API calls for structured data extraction.
"""

import json
import httpx
from typing import Dict, Any, Optional
from app.core.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class LLMService:
    """Service for calling external LLM API to analyze OCR results."""
    
    def __init__(self):
        """Initialize LLM service with API configuration."""
        self.api_url = settings.llm_api_url
        self.api_token = settings.llm_api_token
        self.model = settings.llm_model
        self.timeout = settings.llm_timeout
        self.max_retries = 3
        
        # Validate configuration
        if not self.api_url:
            logger.warning("LLM API URL not configured (missing product_id)")
        if not self.api_token:
            logger.warning("LLM API token not configured")
    
    async def analyze_ocr_content(
        self,
        ocr_content: str,
        introduction: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze OCR content using LLM to extract structured data.
        
        Args:
            ocr_content: The text output from OCR processing
            introduction: User-provided introduction explaining the extraction task
            schema: JSON schema defining expected structure with types and descriptions
            
        Returns:
            Dictionary containing extracted structured data matching the schema
            
        Raises:
            Exception: If LLM API call fails after retries
        """
        logger.info("Starting LLM analysis of OCR content")
        
        # Generate optimized prompt
        prompt = self._build_prompt(ocr_content, introduction, schema)
        
        # Call LLM API with retry logic
        for attempt in range(self.max_retries):
            try:
                result = await self._call_llm_api(prompt, schema)
                logger.info("LLM analysis completed successfully")
                return result
            except Exception as e:
                logger.warning(f"LLM API call attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.error("All LLM API call attempts failed")
                    raise
        
        raise Exception("Failed to analyze OCR content with LLM")
    
    def _build_prompt(
        self,
        ocr_content: str,
        introduction: str,
        schema: Dict[str, Any]
    ) -> str:
        """
        Build optimized prompt for LLM to extract structured data.
        
        Args:
            ocr_content: OCR text output
            introduction: Task explanation
            schema: Expected JSON structure
            
        Returns:
            Complete prompt string
        """
        # Build schema description for prompt
        schema_description = self._format_schema_for_prompt(schema)
        
        # Build task description section (optional)
        task_section = ""
        if introduction and introduction.strip():
            task_section = f"""
TASK DESCRIPTION:
{introduction}
"""
        
        prompt = f"""You are a data extraction assistant. Your task is to analyze the provided OCR text and extract structured information according to the specified schema.
{task_section}
EXPECTED JSON SCHEMA:
{schema_description}

OCR TEXT CONTENT:
{ocr_content}

INSTRUCTIONS:
1. Carefully read the OCR text
2. Extract information according to the schema
3. Return ONLY valid JSON matching the schema
4. If a field is not found, use null for optional fields or appropriate default values
5. Ensure all required fields are present
6. Follow the exact property names and types specified in the schema

OUTPUT FORMAT:
Return only the JSON object, without any additional text or explanation."""

        return prompt
    
    def _format_schema_for_prompt(self, schema: Dict[str, Any]) -> str:
        """
        Format schema into a clear description for the LLM prompt.
        
        Args:
            schema: Schema dictionary with fields and their definitions
            
        Returns:
            Formatted schema description
        """
        lines = ["```json"]
        lines.append("{")
        
        for field_name, field_def in schema.items():
            field_type = field_def.get("type", "string")
            description = field_def.get("description", "")
            required = field_def.get("required", False)
            
            # Add field with description as comment
            req_marker = " (required)" if required else " (optional)"
            lines.append(f'  "{field_name}": {self._type_example(field_type)},  // {description}{req_marker}')
        
        lines.append("}")
        lines.append("```")
        
        return "\n".join(lines)
    
    def _type_example(self, field_type: str) -> str:
        """
        Generate example value for a given type.
        
        Args:
            field_type: Type name (string, number, boolean, array, object)
            
        Returns:
            Example value as string
        """
        type_examples = {
            "string": '"example text"',
            "number": "123",
            "integer": "123",
            "boolean": "true",
            "array": "[]",
            "object": "{}",
            "null": "null"
        }
        return type_examples.get(field_type.lower(), '"value"')
    
    async def _call_llm_api(
        self,
        prompt: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call the external LLM API (Infomaniak).
        
        Args:
            prompt: Complete prompt to send to LLM
            schema: Expected schema for validation
            
        Returns:
            Parsed JSON response from LLM
            
        Raises:
            Exception: If API call fails or response is invalid
        """
        logger.debug(f"Calling LLM API: {self.api_url}")
        
        # Prepare request payload (OpenAI-compatible format)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a precise data extraction assistant. Always return valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Low temperature for consistent extraction
            "max_tokens": 4000
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.api_url,
                json=payload,
                headers=headers
            )
            
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            # Extract content from OpenAI-compatible response
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
            else:
                raise Exception("Invalid response format from LLM API")
            
            # Parse JSON from content
            try:
                # Try to find JSON in response (in case LLM adds extra text)
                content = content.strip()
                if "```json" in content:
                    # Extract JSON from markdown code block
                    start = content.find("```json") + 7
                    end = content.find("```", start)
                    content = content[start:end].strip()
                elif "```" in content:
                    # Extract from generic code block
                    start = content.find("```") + 3
                    end = content.find("```", start)
                    content = content[start:end].strip()
                
                result = json.loads(content)
                
                # Validate result matches schema
                self._validate_result(result, schema)
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response: {str(e)}")
                logger.debug(f"LLM response content: {content}")
                raise Exception(f"LLM returned invalid JSON: {str(e)}")
    
    def _validate_result(
        self,
        result: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> None:
        """
        Validate that result matches expected schema.
        
        Args:
            result: Extracted data from LLM
            schema: Expected schema
            
        Raises:
            Exception: If validation fails
        """
        # Check required fields
        for field_name, field_def in schema.items():
            if field_def.get("required", False) and field_name not in result:
                raise Exception(f"Required field '{field_name}' missing from LLM response")
        
        logger.debug("Result validation passed")
    
    async def shutdown(self):
        """Cleanup resources on service shutdown."""
        logger.info("LLM service shutdown complete")

