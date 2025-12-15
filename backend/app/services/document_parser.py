"""
Document parsing service using the Marker library.
Handles PDF to JSON/Markdown conversion with different processing options.
"""

import asyncio
import json
import time
import gc
import sys
import io
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered
    from marker.renderers.json import JSONRenderer
    from marker.config.parser import ConfigParser
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False
    def create_model_dict():
        raise ImportError("Marker library not installed")
    
    class PdfConverter:
        def __init__(self, *args, **kwargs):
            raise ImportError("Marker library not installed")
    
    class JSONRenderer:
        def __init__(self, *args, **kwargs):
            raise ImportError("Marker library not installed")
    
    class ConfigParser:
        def __init__(self, *args, **kwargs):
            raise ImportError("Marker library not installed")

from app.core.logger import get_logger
from app.core.logger import LoggerMixin
from app.models.enums import OutputFormat
from app.services.marker_log_handler import setup_marker_log_interception, remove_marker_log_interception

logger = get_logger(__name__)


@contextmanager
def capture_tqdm_progress(step_callback, step_name=None, loop=None):
    """
    Context manager to capture tqdm progress bars from stdout/stderr
    and convert them to progress steps.
    
    Marker uses tqdm to show progress bars like:
    - "Recognizing layout: 100%|██████████| 1/1 [00:04<00:00,  4.95s/it]"
    - "Running OCR Error Detection: 100%|██████████| 1/1 [00:00<00:00,  1.98it/s]"
    - "Recognizing tables: 100%|██████████| 1/1 [00:06<00:00,  6.87s/it]"
    
    These don't go through Python logging, so we intercept stdout/stderr.
    ALL steps executed by Marker are captured and displayed as independent steps.
    """
    # Mapping of tqdm progress messages to user-friendly step names
    # All Marker steps are captured - Marker may execute table recognition even if not formatted
    progress_patterns = [
        (r'Recognizing layout', '🔍 Recognizing document layout'),
        (r'Running OCR Error Detection', '🔍 Running OCR error detection'),
        (r'Detecting bboxes', '📦 Detecting bounding boxes'),
        (r'Recognizing tables', '📊 Recognizing tables'),  # Always captured - Marker always runs this
        (r'Extracting text', '📝 Extracting text'),
        (r'Processing pages', '📄 Processing pages'),
    ]
    
    seen_progress = set()
    step_start_times = {}
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    class ProgressInterceptor:
        """Intercept stdout/stderr to capture tqdm progress."""
        def __init__(self, stream, is_stderr=False):
            self.stream = stream
            self.is_stderr = is_stderr
        
        def write(self, text):
            """Intercept writes and parse for tqdm progress."""
            # Write to original stream first
            if text:
                self.stream.write(text)
                self.stream.flush()
                
                # Parse for tqdm progress patterns
                if step_callback and loop:
                    import time
                    # Debug: Log ALL captured text to understand what Marker outputs
                    if text.strip() and len(text.strip()) > 5:  # Ignore empty lines and very short strings
                        logger.debug(f"🔍 [tqdm_capture] Text: {text.strip()[:150]}")
                    
                    for pattern, step_description in progress_patterns:
                        if re.search(pattern, text, re.IGNORECASE):
                            logger.info(f"✅ [tqdm_capture] Pattern matched: '{pattern}' -> '{step_description}'")
                            # Extract progress info (e.g., "100%" or completion status)
                            progress_match = re.search(r'(\d+)%|(\d+)/(\d+)', text)
                            if progress_match:
                                logger.info(f"📊 [tqdm_capture] Progress found: {progress_match.group()}")
                                step_key = f"{step_description}_{pattern}"
                                logger.info(f"🔑 [tqdm_capture] step_key={step_key}, in seen_progress={step_key in seen_progress}, seen_progress={seen_progress}")
                                if step_key not in seen_progress:
                                    seen_progress.add(step_key)
                                    logger.info(f"🔔 [tqdm_capture] First time seeing: {step_description}, calling callback")
                                    # Start step as independent step (not sub-step)
                                    step_start_times[step_description] = time.time()
                                    try:
                                        # Call callback (handles both sync and async)
                                        if step_callback is None:
                                            logger.warning(f"⚠️ [tqdm_capture] step_callback is None!")
                                        elif asyncio.iscoroutinefunction(step_callback):
                                            logger.info(f"📞 [tqdm_capture] Calling ASYNC callback for step {step_description}")
                                            asyncio.run_coroutine_threadsafe(
                                                step_callback(step_description, "in_progress", step_start_times[step_description]),
                                                loop
                                            )
                                        else:
                                            logger.info(f"📞 [tqdm_capture] Calling SYNC callback for step {step_description}")
                                            step_callback(step_description, "in_progress", step_start_times[step_description])
                                    except Exception as e:
                                        logger.warning(f"Failed to call step callback: {e}")
                                else:
                                    # Check if step is completing (100% or final count)
                                    if re.search(r'100%|(\d+)/(\d+)\s+\[.*\]', text):
                                        if step_description in step_start_times:
                                            completion_time = time.time()
                                            try:
                                                # Call callback to complete the step
                                                if asyncio.iscoroutinefunction(step_callback):
                                                    asyncio.run_coroutine_threadsafe(
                                                        step_callback(step_description, "completed", completion_time),
                                                        loop
                                                    )
                                                else:
                                                    step_callback(step_description, "completed", completion_time)
                                            except Exception as e:
                                                logger.warning(f"Failed to call step callback: {e}")
                            break
            
            return len(text) if text else 0
        
        def flush(self):
            if hasattr(self.stream, 'flush'):
                self.stream.flush()
        
        def __getattr__(self, name):
            # Delegate all other attributes to the original stream
            return getattr(self.stream, name)
    
    try:
        # Replace stdout/stderr with interceptors
        sys.stdout = ProgressInterceptor(original_stdout, is_stderr=False)
        sys.stderr = ProgressInterceptor(original_stderr, is_stderr=True)
        yield
    finally:
        # Restore original streams
        sys.stdout = original_stdout
        sys.stderr = original_stderr


def convert_pil_images(data):
    """
    Convert PIL Image objects to dictionaries for Redis serialization.
    
    NOTE: This function is REQUIRED because Marker returns PIL Image objects
    that are not JSON-serializable. Redis requires pure Python dictionaries.
    Marker does NOT handle this conversion natively.
    """
    if hasattr(data, 'size'):  # PIL Image object
        try:
            # Extract width and height from size (can be tuple, list, or indexable)
            size = data.size
            if isinstance(size, (tuple, list)) and len(size) >= 2:
                width = size[0]
                height = size[1]
            elif hasattr(size, '__getitem__') and hasattr(size, '__len__') and len(size) >= 2:
                width = size[0]
                height = size[1]
            else:
                # If size is not indexable, raise exception to fall through to __dict__ handling
                raise ValueError("Size is not indexable")
            
            return {
                "width": width,
                "height": height,
                "format": getattr(data, 'format', 'unknown'),
                "mode": getattr(data, 'mode', 'unknown')
            }
        except (AttributeError, TypeError, IndexError, ValueError):
            # If we can't extract size, raise exception to fall through to __dict__ handling
            raise
    elif isinstance(data, dict):
        return {k: convert_pil_images(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_pil_images(item) for item in data]
    else:
        return data


def serialize_pydantic_objects(data):
    """
    Recursively convert Pydantic objects and other non-serializable objects to pure Python dictionaries.
    
    NOTE: This function is REQUIRED because:
    - Marker returns Pydantic BaseModel objects that must be serialized for Redis
    - Marker returns PIL Image objects that need conversion
    - Redis requires pure JSON-serializable Python types
    
    Marker does NOT handle Redis serialization - this is application-specific logic.
    """
    # Handle basic types and None first (fast path)
    if isinstance(data, (str, int, float, bool, type(None))):
        return data
    
    # Handle Pydantic BaseModel objects
    if hasattr(data, 'model_dump'):
        try:
            return serialize_pydantic_objects(data.model_dump())
        except Exception:
            pass
    
    # Handle PIL Images SECOND (before __dict__ check, as PIL Images also have __dict__)
    # Check for PIL Image by looking for 'size' attribute and typical PIL attributes
    # This must come before __dict__ check to avoid treating PIL Images as generic objects
    if hasattr(data, 'size') and hasattr(data, 'format') and hasattr(data, 'mode'):
        # Try to convert as PIL Image - convert_pil_images handles the conversion logic
        try:
            result = convert_pil_images(data)
            # Only return if we got a proper dict with width/height, not the original data object
            if isinstance(result, dict) and 'width' in result:
                return result
        except Exception:
            # If conversion fails, fall through to __dict__ handling
            pass
    
    # Handle dict_like objects with __dict__
    # This must come AFTER PIL Image check
    # Exclude objects that look like PIL Images (have size, format, mode)
    if (hasattr(data, '__dict__') and 
        not isinstance(data, (str, int, float, bool, type(None))) and
        not (hasattr(data, 'size') and hasattr(data, 'format') and hasattr(data, 'mode'))):
        try:
            obj_dict = {}
            for key, value in data.__dict__.items():
                if not key.startswith('_'):  # Skip private attributes
                    obj_dict[key] = serialize_pydantic_objects(value)
            return obj_dict
        except Exception:
            pass
    
    # Handle dictionaries
    if isinstance(data, dict):
        return {k: serialize_pydantic_objects(v) for k, v in data.items()}
    
    # Handle lists and tuples
    if isinstance(data, (list, tuple)):
        return [serialize_pydantic_objects(item) for item in data]
    
    # For anything else, try to convert to string as fallback
    try:
        return str(data)
    except Exception:
        return None


class DocumentParserService:
    """
    Service for parsing documents using the Marker library.
    Handles PDF conversion to markdown/JSON with caching and error recovery.
    """
    
    def __init__(self):
        self.models_dict = None
        self.models_ready = False
        self.model_load_error = None
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    def _build_marker_config(
        self,
        output_format: str,
        force_ocr: bool = False,
        extract_images: bool = False,
        paginate_output: bool = False,
        language: Optional[str] = None
    ) -> dict:
        """
        Build Marker configuration dictionary from processing options.
        
        Args:
            output_format: "json" or "markdown"
            force_ocr: Force OCR even if text is extractable
            extract_images: Extract and include images
            paginate_output: Add page separators in output
            language: Document language hint
            
        Returns:
            Configuration dictionary for Marker ConfigParser
        """
        config = {
            "output_format": output_format,
        }
        
        # OCR settings
        if force_ocr:
            config["force_ocr"] = True
        
        # Image extraction settings
        config["disable_image_extraction"] = not extract_images
        
        # Pagination settings - adds page separators in markdown output
        config["paginate_output"] = paginate_output
        
        # Language hint
        if language and language != 'auto':
            config["langs"] = [language]
        
        logger.debug(f"Marker config: {config}")
        return config
    
    async def initialize_models(self, progress_callback=None) -> bool:
        """
        Initialize Marker models with progress tracking.
        
        Returns:
            bool: True if models loaded successfully, False otherwise
        """
        if not MARKER_AVAILABLE:
            error_msg = "Marker library not installed"
            logger.error(error_msg)
            self.model_load_error = error_msg
            return False
        
        if self.models_ready:
            logger.info("Models already initialized")
            return True
        
        try:
            logger.info("Starting Marker model initialization...")
            
            # Update progress
            if progress_callback:
                await progress_callback(10, "Loading Marker models...")
            
            # Create models in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            
            def _create_models():
                try:
                    return create_model_dict()
                except Exception as e:
                    logger.error(f"Failed to create model dict: {str(e)}")
                    raise
            
            # Load models with timeout
            try:
                self.models_dict = await asyncio.wait_for(
                    loop.run_in_executor(self.executor, _create_models),
                    timeout=300  # 5 minutes timeout
                )
                
                if progress_callback:
                    await progress_callback(90, "Models loaded, verifying...")
                
                # Test model initialization by creating a converter
                await self._test_converter_creation()
                
                self.models_ready = True
                if progress_callback:
                    await progress_callback(100, "Models ready!")
                    
                logger.info("Marker models initialized successfully")
                return True
                
            except asyncio.TimeoutError:
                error_msg = "Marker model loading timed out after 5 minutes"
                logger.error(error_msg)
                self.model_load_error = error_msg
                return False
                
        except Exception as e:
            error_msg = f"Failed to initialize models: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.model_load_error = error_msg
            return False
    
    async def _test_converter_creation(self):
        """Test that we can create a PdfConverter without errors."""
        try:
            # Simple test creation
            loop = asyncio.get_event_loop()
            
            def _test_create():
                converter = PdfConverter(artifact_dict=self.models_dict)
                return True
            
            await loop.run_in_executor(self.executor, _test_create)
            logger.info("PdfConverter test creation successful")
            
        except Exception as e:
            logger.error(f"PdfConverter test creation failed: {str(e)}")
            raise RuntimeError(f"Converter creation test failed: {str(e)}")
    
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
        Parse a document using Marker.
        
        Args:
            file_path: Path to the PDF file
            output_format: Output format (json/markdown/both)
            force_ocr: Force OCR even if text is extractable
            extract_images: Extract and include images in the output
            paginate_output: Add page separators in output
            language: Document language hint (ISO 639-1 code, e.g., 'en', 'fr')
            step_callback: Optional callback function(step_name, status) for tracking progress
            
        Returns:
            Dictionary containing parsed content and metadata
        """
        # Helper to call step callback if provided
        async def update_step(step_name: str, status: str, timestamp_or_substep = None):
            if step_callback:
                await step_callback(step_name, status, timestamp_or_substep)
        
        # Verify models are ready - no fallback, must be initialized at startup
        if not self.models_ready:
            error_msg = "AI models are not loaded. Models must be initialized at startup."
            if self.model_load_error:
                error_msg += f" Error: {self.model_load_error}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting document parsing: {file_path}")
            logger.info(f"🔍 parse_document received step_callback: {step_callback is not None}")
            
            # Process document in thread pool
            loop = asyncio.get_event_loop()
            
            # Set up Marker log interception to capture internal execution details
            marker_log_handler = None
            if step_callback:
                try:
                    # Use step_callback directly - steps are now main steps, not sub-steps
                    marker_log_handler = setup_marker_log_interception(
                        step_callback=step_callback,
                        step_name=None,
                        event_loop=loop
                    )
                    logger.info("✅ Marker log interception enabled for detailed progress tracking")
                except Exception as e:
                    logger.warning(f"Failed to set up Marker log interception: {e}")
            
            def _process_document():
                try:
                    # Determine what to generate based on output_format parameter
                    need_json = output_format in [OutputFormat.JSON, OutputFormat.BOTH]
                    need_markdown = output_format in [OutputFormat.MARKDOWN, OutputFormat.BOTH]
                    
                    logger.info(f"Processing with options: format={output_format.value}, "
                               f"force_ocr={force_ocr}, images={extract_images}, paginate_output={paginate_output}, lang={language}")
                    
                    rich_structure = None
                    markdown_content = ""
                    json_rendered = None
                    markdown_rendered = None
                    
                    # 1. Process document - Generate formats
                    logger.info("🎯 Starting document processing...")
                    
                    # Step: JSON format if requested
                    if need_json:
                        logger.info("🎯 Generating native JSON format...")
                        
                        json_config = self._build_marker_config(
                            output_format="json",
                            force_ocr=force_ocr,
                            extract_images=extract_images,
                            paginate_output=paginate_output,
                            language=language
                        )
                        json_config_parser = ConfigParser(json_config)
                        
                        json_converter = PdfConverter(
                            config=json_config_parser.generate_config_dict(),
                            artifact_dict=self.models_dict,
                            processor_list=json_config_parser.get_processors(),
                            renderer=json_config_parser.get_renderer()
                        )
                        
                        # Real processing happens here
                        # Marker steps are automatically detected by capture_tqdm_progress
                        # Wrapper to call step_callback (async) from tqdm interception
                        async def tqdm_callback_json(step_name: str, status: str, substep: str = None):
                            await step_callback(step_name, status, substep)
                        
                        with capture_tqdm_progress(tqdm_callback_json, None, loop):
                            json_rendered = json_converter(file_path)
                        
                        # Extract and serialize native JSON structure
                        if hasattr(json_rendered, 'children') and hasattr(json_rendered, 'block_type'):
                            rich_structure = serialize_pydantic_objects({
                                "block_type": json_rendered.block_type,
                                "id": getattr(json_rendered, 'id', '/document/0'),
                                "children": json_rendered.children,
                            })
                            logger.info(f"✅ JSON generated: {json_rendered.block_type} with {len(json_rendered.children) if hasattr(json_rendered, 'children') else 0} children")
                        else:
                            rich_structure = None
                            logger.warning("⚠️ JSON structure not as expected")
                        
                        # Cleanup JSON converter
                        del json_converter
                        gc.collect()
                        logger.info("✅ JSON structure generated")
                    
                    # Step: Markdown format if requested
                    if need_markdown:
                        logger.info("📝 Generating markdown format...")
                        markdown_config = self._build_marker_config(
                            output_format="markdown",
                            force_ocr=force_ocr,
                            extract_images=extract_images,
                            paginate_output=paginate_output,
                            language=language
                        )
                        markdown_config_parser = ConfigParser(markdown_config)
                        
                        # Note: Marker always runs table recognition internally as part of the processing pipeline.
                        # The paginate_output option only controls whether page separators are added to the output.
                        # All Marker steps are displayed in progress, including table recognition.
                        markdown_converter = PdfConverter(
                            config=markdown_config_parser.generate_config_dict(),
                            artifact_dict=self.models_dict,
                            processor_list=markdown_config_parser.get_processors(),
                            renderer=markdown_config_parser.get_renderer()
                        )
                        
                        # Real processing happens here
                        # Marker steps are automatically detected by capture_tqdm_progress
                        # Wrapper to call step_callback (async) from tqdm interception  
                        async def tqdm_callback(step_name: str, status: str, substep: str = None):
                            await step_callback(step_name, status, substep)
                        
                        # Capture ALL Marker steps - Marker may execute table recognition even if not formatted
                        with capture_tqdm_progress(tqdm_callback, None, loop):
                            markdown_rendered = markdown_converter(file_path)
                        
                        # Extract markdown content
                        if hasattr(markdown_rendered, 'markdown'):
                            markdown_content = markdown_rendered.markdown
                            logger.info(f"✅ Markdown generated: {len(markdown_content)} characters")
                        else:
                            # Fallback with text_from_rendered
                            markdown_content, _, _ = text_from_rendered(markdown_rendered)
                            logger.info("✅ Markdown via text_from_rendered fallback")
                        
                        # Cleanup markdown converter
                        del markdown_converter
                        gc.collect()
                        logger.info("✅ Markdown generated")
                    
                    # 2. Extract metadata and images from whichever format was generated
                    metadata = {}
                    images = {}
                    
                    if json_rendered:
                        metadata = getattr(json_rendered, 'metadata', {})
                        images = getattr(json_rendered, 'images', {})
                    elif markdown_rendered:
                        metadata = getattr(markdown_rendered, 'metadata', {})
                        images = getattr(markdown_rendered, 'images', {})
                    
                    # Serialize non-serializable objects for Redis
                    images = serialize_pydantic_objects(images)
                    metadata = serialize_pydantic_objects(metadata)
                    
                    logger.info(f"🎉 Successfully generated requested format(s): {output_format.value}")
                    
                    # Prepare result based on what was actually generated
                    result = {
                        "metadata": metadata,
                        "images": images,
                        "processing_time": None  # Will be set below
                    }
                    
                    # Only include generated formats
                    if need_markdown:
                        result["text"] = markdown_content
                        result["markdown_content"] = markdown_content
                    else:
                        result["text"] = ""
                        result["markdown_content"] = None
                    
                    if need_json:
                        result["rich_structure"] = rich_structure
                    else:
                        result["rich_structure"] = None
                    
                    # Final cleanup
                    if json_rendered:
                        del json_rendered
                    if markdown_rendered:
                        del markdown_rendered
                    gc.collect()
                    logger.info("🧹 Memory cleanup completed")
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Dual format processing failed, trying fallback: {str(e)}")
                    
                    # Fallback: return markdown only without rich structure
                    try:
                        converter = PdfConverter(artifact_dict=self.models_dict)
                        rendered = converter(file_path)
                        text, metadata, images = text_from_rendered(rendered)
                        
                        # Sérialiser les objets non-sérialisables
                        metadata = serialize_pydantic_objects(metadata)
                        images = serialize_pydantic_objects(images)
                        
                        # No rich_structure in fallback - rely on native JSON generation or return None
                        logger.warning("Fallback mode: returning markdown without rich structure")
                        
                        result = {
                            "text": text,
                            "markdown_content": text,
                            "rich_structure": None,  # Fallback doesn't generate rich structure
                            "metadata": metadata,
                            "images": images,
                            "processing_time": None
                        }
                        
                        # 🧹 Force garbage collection
                        del converter, rendered
                        gc.collect()
                        
                        return result
                    except Exception as fallback_error:
                        logger.error(f"Fallback also failed: {str(fallback_error)}")
                        raise RuntimeError(f"All processing methods failed: {str(e)}, {str(fallback_error)}")
            
            # Execute with timeout
            result = await asyncio.wait_for(
                loop.run_in_executor(self.executor, _process_document),
                timeout=600  # 10 minutes timeout
            )
            
            # Step updates are now sent in real-time from the thread
            # No need to process accumulated updates
            
            # Clean up Marker log interception
            if marker_log_handler:
                try:
                    remove_marker_log_interception(marker_log_handler)
                    logger.debug("Marker log interception removed")
                except Exception as e:
                    logger.warning(f"Failed to remove Marker log interception: {e}")
            
            # Processing time calculation (no separate step needed)
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            
            logger.info(f"Document parsing completed in {processing_time:.2f}s")
            return result
            
        except asyncio.TimeoutError:
            error_msg = "Document processing timed out after 10 minutes"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        except Exception as e:
            error_msg = f"Marker processing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        Get current model status.
        
        Returns:
            Dictionary with model status information
        """
        if not MARKER_AVAILABLE:
            return {
                "status": "error",
                "message": "Marker library not installed",
                "models_loaded": False,
                "error": "Marker library not installed"
            }
        
        if self.models_ready:
            return {
                "status": "ready",
                "message": "Models loaded and ready",
                "models_loaded": True,
                "error": None
            }
        elif self.model_load_error:
            return {
                "status": "error",
                "message": self.model_load_error,
                "models_loaded": False,
                "error": self.model_load_error
            }
        else:
            return {
                "status": "loading",
                "message": "Models are being loaded...",
                "models_loaded": False,
                "error": None
            }
    
    async def shutdown(self):
        """Clean up resources."""
        if self.executor:
            self.executor.shutdown(wait=True)
            logger.info("DocumentParserService shutdown complete") 