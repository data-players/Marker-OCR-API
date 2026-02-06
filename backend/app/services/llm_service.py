"""
LLM service for post-OCR analysis with external LLM API (Infomaniak).
Handles prompt generation and API calls for structured data extraction.
"""

import json
import httpx
from typing import Dict, Any, Optional, List
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
        
        # Build list of ALL expected field names for emphasis
        all_fields = self._get_all_field_names(schema)
        fields_list = ", ".join(f'"{f}"' for f in all_fields) if all_fields else "as defined in schema"
        
        prompt = f"""You are a precise data extraction assistant. Extract structured information from OCR text following the EXACT schema provided.
{task_section}
EXPECTED JSON SCHEMA:
{schema_description}

CRITICAL RULES - YOU MUST FOLLOW THESE EXACTLY:
1. **USE EXACT FIELD NAMES**: Your output MUST use these exact field names: {fields_list}
   - DO NOT rename fields (e.g., use "supplier" NOT "vendor", use "prix_unitaire" NOT "unit_price")
   - DO NOT translate field names
   - DO NOT invent new field names

2. **EXTRACT ALL FIELDS**: You MUST include ALL fields from the schema in your response:
   - Required fields: extract from text or return reasonable value
   - Optional fields: extract from text or return null
   - NEVER skip a field that exists in the schema

3. **MATCH TYPES EXACTLY**:
   - string: return text as string
   - number: return numeric value (can have decimals)
   - integer: return whole number
   - boolean: return true or false
   - array: return a list []
   - object: return an object {{}}

OCR TEXT CONTENT:
{ocr_content}

OUTPUT:
Return ONLY a valid JSON object. No explanations, no markdown, no extra text.
The JSON MUST contain exactly these top-level fields: {fields_list}"""

        return prompt
    
    def _get_all_field_names(self, schema: Dict[str, Any], prefix: str = "") -> List[str]:
        """
        Extract all field names from schema (top-level only for emphasis).
        
        Args:
            schema: Schema dictionary with type, properties/items
            prefix: Path prefix for nested fields
            
        Returns:
            List of field names
        """
        fields = []
        root_type = schema.get("type", "object")
        
        if root_type == "object":
            properties = schema.get("properties", {})
            for field_name in properties.keys():
                fields.append(field_name)
        elif root_type == "array":
            items = schema.get("items", {})
            if items.get("type") == "object":
                item_properties = items.get("properties", {})
                for field_name in item_properties.keys():
                    fields.append(f"[].{field_name}")
        
        return fields
    
    def _format_schema_for_prompt(self, schema: Dict[str, Any]) -> str:
        """
        Format schema into a clear description for the LLM prompt.
        Supports nested objects and arrays, including root type handling.
        
        Args:
            schema: Schema dictionary with type, properties/items
            
        Returns:
            Formatted schema description as JSON with comments
        """
        # Get root type (object or array)
        root_type = schema.get("type", "object")
        
        # Build example JSON structure based on root type
        if root_type == "array":
            items = schema.get("items", {})
            item_type = items.get("type", "object") if items else "object"
            
            if item_type == "object":
                # Array of objects - use items.properties
                item_properties = items.get("properties", {})
                example_item = self._build_example_structure(item_properties)
                example = [example_item]
                descriptions = f"Array of objects with properties:\n{self._build_field_descriptions(item_properties, '[].') if item_properties else 'No properties defined'}"
            else:
                # Array of primitives
                example = [self._type_example(item_type)]
                descriptions = f"Array of {item_type} values"
        else:
            # Object root type
            properties = schema.get("properties", {})
            example = self._build_example_structure(properties)
            descriptions = self._build_field_descriptions(properties)
        
        json_str = json.dumps(example, indent=2)
        
        result = f"```json\n{json_str}\n```\n\nField descriptions:\n{descriptions}"
        return result
    
    def _build_example_structure(
        self, 
        schema: Dict[str, Any], 
        depth: int = 0
    ) -> Dict[str, Any]:
        """
        Build an example JSON structure from schema.
        
        Args:
            schema: Schema dictionary
            depth: Current nesting depth (for limiting recursion)
            
        Returns:
            Example structure dictionary
        """
        if depth > 5:  # Limit recursion depth
            return {}
        
        example = {}
        for field_name, field_def in schema.items():
            field_type = field_def.get("type", "string")
            example[field_name] = self._get_type_example(field_def, depth)
        
        return example
    
    def _get_type_example(self, field_def: Dict[str, Any], depth: int = 0) -> Any:
        """
        Generate example value based on field definition.
        
        Args:
            field_def: Field definition with type, items, properties
            depth: Current nesting depth
            
        Returns:
            Example value matching the type
        """
        field_type = field_def.get("type", "string")
        
        if field_type == "object":
            # Nested object with properties
            properties = field_def.get("properties", {})
            if properties and depth < 5:
                return self._build_example_structure(properties, depth + 1)
            return {}
        
        elif field_type == "array":
            # Array with items definition
            items = field_def.get("items", {})
            item_type = items.get("type", "string") if items else "string"
            
            if item_type == "object":
                # Array of objects
                item_properties = items.get("properties", {})
                if item_properties and depth < 5:
                    return [self._build_example_structure(item_properties, depth + 1)]
                return [{}]
            else:
                # Array of primitives
                return [self._type_example(item_type)]
        
        else:
            # Primitive types
            return self._type_example(field_type)
    
    def _build_field_descriptions(
        self, 
        schema: Dict[str, Any], 
        prefix: str = ""
    ) -> str:
        """
        Build human-readable field descriptions.
        
        Args:
            schema: Schema dictionary
            prefix: Path prefix for nested fields
            
        Returns:
            Formatted descriptions string
        """
        lines = []
        
        for field_name, field_def in schema.items():
            full_path = f"{prefix}{field_name}" if prefix else field_name
            field_type = field_def.get("type", "string")
            description = field_def.get("description", "")
            required = field_def.get("required", False)
            
            req_marker = " [REQUIRED]" if required else ""
            type_display = field_type.upper()
            
            # Handle array type display
            if field_type == "array":
                items = field_def.get("items", {})
                item_type = items.get("type", "string") if items else "string"
                type_display = f"ARRAY of {item_type.upper()}"
            
            lines.append(f"- {full_path} ({type_display}){req_marker}: {description}")
            
            # Recurse into nested objects
            if field_type == "object":
                properties = field_def.get("properties", {})
                if properties:
                    lines.append(self._build_field_descriptions(properties, f"{full_path}."))
            
            # Recurse into array item objects
            if field_type == "array":
                items = field_def.get("items", {})
                if items and items.get("type") == "object":
                    item_properties = items.get("properties", {})
                    if item_properties:
                        lines.append(self._build_field_descriptions(item_properties, f"{full_path}[]."))
        
        return "\n".join(lines)
    
    def _type_example(self, field_type: str) -> Any:
        """
        Generate example value for a primitive type.
        
        Args:
            field_type: Type name (string, number, boolean)
            
        Returns:
            Example value
        """
        type_examples = {
            "string": "example text",
            "number": 123.45,
            "integer": 123,
            "boolean": True,
            "null": None
        }
        return type_examples.get(field_type.lower(), "value")
    
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
        system_message = """You are a precise data extraction assistant. Your responses must:
1. Be valid JSON only - no explanations, no markdown
2. Use EXACTLY the field names provided in the schema - never rename or translate them
3. Include ALL fields from the schema - never skip fields
4. Match the exact types specified (string, number, array, object, etc.)

CRITICAL: Use the EXACT field names from the schema. Do not substitute with synonyms or translations."""
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_message
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
        result: Any,
        schema: Dict[str, Any],
        path: str = ""
    ) -> None:
        """
        Validate that result matches expected schema (recursive for nested structures).
        Supports root type validation (object or array).
        
        Args:
            result: Extracted data from LLM
            schema: Expected schema with type, properties/items
            path: Current path for error messages
            
        Raises:
            Exception: If validation fails
        """
        root_type = schema.get("type", "object")
        
        # Handle root-level array type
        if root_type == "array" and not path:
            if not isinstance(result, list):
                raise Exception(f"Expected array at root, got {type(result).__name__}")
            
            items_def = schema.get("items", {})
            if items_def:
                item_type = items_def.get("type", "string")
                if item_type == "object":
                    item_properties = items_def.get("properties", {})
                    if item_properties:
                        for i, item in enumerate(result):
                            self._validate_properties(item, item_properties, f"[{i}]")
            
            logger.debug("Root array validation passed")
            return
        
        # Handle root-level object type
        if root_type == "object" and not path:
            if not isinstance(result, dict):
                raise Exception(f"Expected object at root, got {type(result).__name__}")
            
            properties = schema.get("properties", {})
            if properties:
                self._validate_properties(result, properties, "")
            
            logger.debug("Root object validation passed")
            return
        
        # Fallback for nested validation (called with properties directly)
        if isinstance(result, dict):
            self._validate_properties(result, schema, path)
    
    def _validate_properties(
        self,
        result: Dict[str, Any],
        properties: Dict[str, Any],
        path: str = ""
    ) -> None:
        """
        Validate object properties against schema.
        
        Args:
            result: Object data from LLM
            properties: Expected properties schema
            path: Current path for error messages
        """
        if not isinstance(result, dict):
            raise Exception(f"Expected object at '{path}', got {type(result).__name__}")
        
        # Check required fields and validate nested structures
        for field_name, field_def in properties.items():
            field_path = f"{path}.{field_name}" if path else field_name
            
            if field_def.get("required", False) and field_name not in result:
                raise Exception(f"Required field '{field_path}' missing from LLM response")
            
            if field_name in result:
                value = result[field_name]
                field_type = field_def.get("type", "string")
                
                # Validate nested object
                if field_type == "object" and value is not None:
                    nested_properties = field_def.get("properties", {})
                    if nested_properties and isinstance(value, dict):
                        self._validate_properties(value, nested_properties, field_path)
                
                # Validate array items
                if field_type == "array" and value is not None:
                    items_def = field_def.get("items", {})
                    if items_def and isinstance(value, list):
                        item_type = items_def.get("type", "string")
                        if item_type == "object":
                            item_properties = items_def.get("properties", {})
                            if item_properties:
                                for i, item in enumerate(value):
                                    self._validate_properties(
                                        item, 
                                        item_properties, 
                                        f"{field_path}[{i}]"
                                    )
        
        logger.debug(f"Validation passed{' for ' + path if path else ''}")
    
    async def extract_with_schema(
        self,
        text: str,
        schema: Dict[str, Any],
        introduction: str = ""
    ) -> Dict[str, Any]:
        """
        Convenience method to extract structured data from text.
        
        Args:
            text: Text content to analyze
            schema: JSON schema defining fields to extract
            introduction: Optional task instructions
            
        Returns:
            Extracted data matching the schema
        """
        return await self.analyze_ocr_content(
            ocr_content=text,
            introduction=introduction,
            schema=schema
        )
    
    async def shutdown(self):
        """Cleanup resources on service shutdown."""
        logger.info("LLM service shutdown complete")
