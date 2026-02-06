"""
Document parsing service using Datalab's cloud Marker API.
Handles PDF to JSON/Markdown conversion via HTTP API calls.
"""

import asyncio
import time
import aiohttp
from pathlib import Path
from typing import Dict, Any, Optional

from app.core.logger import get_logger
from app.core.config import settings
from app.models.enums import OutputFormat
from app.services.document_parser_interface import DocumentParserInterface

logger = get_logger(__name__)


class DocumentParserAPIService(DocumentParserInterface):
    """
    Service for parsing documents using Datalab's cloud Marker API.
    
    This is a lightweight alternative to the library-based service that:
    - Does not require GPU or heavy ML dependencies
    - Sends documents to Datalab's cloud for processing
    - Polls for results asynchronously
    """
    
    def __init__(self):
        self.api_key = settings.datalab_api_key
        self.base_url = settings.datalab_api_base_url
        self.timeout = settings.datalab_api_timeout
        self.poll_interval = settings.datalab_api_poll_interval
        self.mode = settings.datalab_api_mode
        self.initialized = False
        self.init_error = None
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def initialize_models(self, progress_callback=None) -> bool:
        """
        Validate API key and connectivity for API mode.
        No models to load, just verify configuration.
        """
        if progress_callback:
            await progress_callback(10, "Validating Datalab API configuration...")
        
        # Check if API key is configured
        if not self.api_key:
            self.init_error = "Datalab API key not configured (set DATALAB_API_KEY)"
            logger.error(self.init_error)
            return False
        
        try:
            if progress_callback:
                await progress_callback(50, "Testing Datalab API connectivity...")
            
            # Test API connectivity with health endpoint
            session = await self._get_session()
            headers = {"X-API-Key": self.api_key}
            
            async with session.get(
                f"{self.base_url.rstrip('/').replace('/api/v1', '')}/api/v1/health",
                headers=headers
            ) as response:
                if response.status == 200:
                    self.initialized = True
                    if progress_callback:
                        await progress_callback(100, "Datalab API ready!")
                    logger.info("Datalab API connection validated successfully")
                    return True
                else:
                    # API might not have a health endpoint, but that's OK
                    # Just check that we can reach the service
                    self.initialized = True
                    if progress_callback:
                        await progress_callback(100, "Datalab API configuration validated")
                    logger.info("Datalab API configuration validated (health check returned non-200)")
                    return True
                    
        except aiohttp.ClientError as e:
            self.init_error = f"Failed to connect to Datalab API: {str(e)}"
            logger.error(self.init_error)
            # Still mark as initialized - we'll handle errors during actual requests
            self.initialized = True
            if progress_callback:
                await progress_callback(100, "Datalab API configured (connectivity pending)")
            return True
        except Exception as e:
            self.init_error = f"Datalab API initialization error: {str(e)}"
            logger.error(self.init_error, exc_info=True)
            return False
    
    def _map_output_format(self, output_format: OutputFormat) -> str:
        """Map internal output format to Datalab API format."""
        if output_format == OutputFormat.JSON:
            return "json"
        return "markdown"
    
    async def _submit_document(
        self,
        file_path: str,
        output_format: OutputFormat,
        force_ocr: bool,
        paginate_output: bool,
        language: Optional[str]
    ) -> Dict[str, Any]:
        """
        Submit a document to Datalab API for processing.
        
        Returns:
            dict with request_id and request_check_url
        """
        session = await self._get_session()
        headers = {"X-API-Key": self.api_key}
        
        # Prepare form data
        data = aiohttp.FormData()
        
        # Add file
        file_path_obj = Path(file_path)
        data.add_field(
            'file',
            open(file_path, 'rb'),
            filename=file_path_obj.name,
            content_type='application/pdf'
        )
        
        # Add parameters
        data.add_field('mode', self.mode)
        data.add_field('output_format', self._map_output_format(output_format))
        
        if paginate_output:
            data.add_field('paginate', 'true')
        
        # Note: force_ocr is deprecated in Datalab API, OCR is handled automatically
        # Note: language/langs is deprecated in Datalab API
        
        logger.info(f"Submitting document to Datalab API: {file_path_obj.name}")
        logger.debug(f"API params: mode={self.mode}, output_format={self._map_output_format(output_format)}")
        
        async with session.post(
            f"{self.base_url}/marker",
            headers=headers,
            data=data
        ) as response:
            if response.status == 403:
                error_data = await response.json()
                detail = error_data.get('detail', 'Access forbidden')
                if 'subscription' in detail.lower():
                    raise RuntimeError(
                        "Datalab API requires an active paid subscription. "
                        "Please visit https://www.datalab.to to subscribe, "
                        "or switch to MARKER_MODE=library for local processing."
                    )
                raise RuntimeError(f"Datalab API access denied: {detail}")
            
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Datalab API submission failed ({response.status}): {error_text}")
            
            result = await response.json()
            
            if not result.get('success', True):
                raise RuntimeError(f"Datalab API error: {result.get('error', 'Unknown error')}")
            
            logger.info(f"Document submitted, request_id: {result.get('request_id')}")
            return result
    
    async def _poll_for_result(
        self,
        request_id: str,
        step_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Poll Datalab API until the result is ready.
        
        Args:
            request_id: The request ID from submission
            step_callback: Optional callback for progress updates
            
        Returns:
            Final result from the API
        """
        session = await self._get_session()
        headers = {"X-API-Key": self.api_key}
        url = f"{self.base_url}/marker/{request_id}"
        
        start_time = time.time()
        poll_count = 0
        
        while True:
            poll_count += 1
            elapsed = time.time() - start_time
            
            if elapsed > self.timeout:
                raise RuntimeError(f"Datalab API timeout after {self.timeout}s")
            
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Datalab API poll failed ({response.status}): {error_text}")
                
                result = await response.json()
            
            status = result.get('status', 'unknown')
            logger.debug(f"Poll #{poll_count}: status={status}, elapsed={elapsed:.1f}s")
            
            if status == 'complete':
                logger.info(f"Document processing complete after {elapsed:.1f}s")
                return result
            
            if status == 'error' or status == 'failed':
                error_msg = result.get('error', 'Processing failed')
                raise RuntimeError(f"Datalab API processing error: {error_msg}")
            
            # Update progress if callback provided
            if step_callback:
                try:
                    progress_msg = f"🔄 Processing... ({elapsed:.0f}s elapsed)"
                    if asyncio.iscoroutinefunction(step_callback):
                        await step_callback(progress_msg, "in_progress", time.time())
                    else:
                        step_callback(progress_msg, "in_progress", time.time())
                except Exception as e:
                    logger.warning(f"Step callback error: {e}")
            
            # Wait before next poll
            await asyncio.sleep(self.poll_interval)
    
    def _convert_api_result(
        self,
        api_result: Dict[str, Any],
        output_format: OutputFormat,
        processing_time: float
    ) -> Dict[str, Any]:
        """
        Convert Datalab API result to our internal format.
        
        Datalab API returns:
        - status, output_format
        - chunks: {}, json: {}, markdown: string, html: string
        - images: {}, metadata: {}, success: bool
        """
        result = {
            "text": "",
            "markdown_content": None,
            "rich_structure": None,
            "metadata": api_result.get("metadata", {}),
            "images": api_result.get("images", {}),
            "processing_time": processing_time
        }
        
        # Extract content based on output format
        if output_format == OutputFormat.MARKDOWN:
            markdown = api_result.get("markdown", "")
            result["text"] = markdown
            result["markdown_content"] = markdown
        
        elif output_format == OutputFormat.JSON:
            json_data = api_result.get("json", {})
            result["rich_structure"] = json_data
            # Also provide markdown if available
            if "markdown" in api_result:
                result["text"] = api_result["markdown"]
                result["markdown_content"] = api_result["markdown"]
        
        return result
    
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
        Parse a document using Datalab's cloud Marker API.
        
        Submits the document, polls for completion, and returns results.
        """
        if not self.initialized:
            raise RuntimeError("Datalab API service not initialized")
        
        if not self.api_key:
            raise RuntimeError("Datalab API key not configured")
        
        start_time = time.time()
        
        try:
            # Report initial step
            if step_callback:
                try:
                    if asyncio.iscoroutinefunction(step_callback):
                        await step_callback("📤 Uploading to Datalab API", "in_progress", start_time)
                    else:
                        step_callback("📤 Uploading to Datalab API", "in_progress", start_time)
                except Exception as e:
                    logger.warning(f"Step callback error: {e}")
            
            # Submit document
            submission = await self._submit_document(
                file_path=file_path,
                output_format=output_format,
                force_ocr=force_ocr,
                paginate_output=paginate_output,
                language=language
            )
            
            request_id = submission.get("request_id")
            if not request_id:
                raise RuntimeError("No request_id in API response")
            
            # Report upload complete
            if step_callback:
                try:
                    if asyncio.iscoroutinefunction(step_callback):
                        await step_callback("📤 Uploading to Datalab API", "completed", time.time())
                        await step_callback("⏳ Processing document", "in_progress", time.time())
                    else:
                        step_callback("📤 Uploading to Datalab API", "completed", time.time())
                        step_callback("⏳ Processing document", "in_progress", time.time())
                except Exception as e:
                    logger.warning(f"Step callback error: {e}")
            
            # Poll for result
            api_result = await self._poll_for_result(request_id, step_callback)
            
            processing_time = time.time() - start_time
            
            # Report completion
            if step_callback:
                try:
                    if asyncio.iscoroutinefunction(step_callback):
                        await step_callback("⏳ Processing document", "completed", time.time())
                    else:
                        step_callback("⏳ Processing document", "completed", time.time())
                except Exception as e:
                    logger.warning(f"Step callback error: {e}")
            
            # Convert to internal format
            result = self._convert_api_result(api_result, output_format, processing_time)
            
            logger.info(f"Document processed via Datalab API in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Datalab API processing failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Datalab API processing failed: {str(e)}")
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        Get current API service status.
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "Datalab API key not configured",
                "models_loaded": False,
                "error": "Set DATALAB_API_KEY environment variable",
                "mode": "api"
            }
        
        if self.initialized:
            return {
                "status": "ready",
                "message": f"Datalab API ready (mode: {self.mode})",
                "models_loaded": True,
                "error": self.init_error,
                "mode": "api"
            }
        else:
            return {
                "status": "error" if self.init_error else "loading",
                "message": self.init_error or "Initializing Datalab API connection...",
                "models_loaded": False,
                "error": self.init_error,
                "mode": "api"
            }
    
    async def shutdown(self):
        """Clean up resources (close HTTP session)."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("DocumentParserAPIService shutdown complete")
