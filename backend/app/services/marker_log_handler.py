"""
Custom logging handler to intercept Marker library logs and convert them to progress updates.
This allows tracking Marker's internal execution details in real-time.
"""

import logging
import re
import asyncio
import time
from typing import Optional, Callable, Any
from queue import Queue
import threading


class MarkerLogHandler(logging.Handler):
    """
    Custom logging handler that intercepts Marker library logs
    and converts them to progress step updates.
    """
    
    # Mapping of Marker log patterns to user-friendly step descriptions
    # More detailed patterns for rendering operations
    # Patterns are ordered by specificity (most specific first)
    STEP_PATTERNS = [
        # Page-specific operations (most specific)
        (r'processing.*page\s+(\d+)|page\s+(\d+).*processing|page\s*:\s*(\d+).*processing', '📄 Processing page'),
        (r'page\s+(\d+).*rendering|rendering.*page\s+(\d+)', '🎨 Rendering page'),
        (r'page\s+(\d+).*ocr|ocr.*page\s+(\d+)', '🔍 Running OCR on page'),
        
        # Specific rendering operations
        (r'rendering.*markdown|markdown.*render|render.*markdown', '🎨 Rendering Markdown output'),
        (r'converting.*to.*markdown|markdown.*conversion|convert.*markdown', '🔄 Converting to Markdown'),
        (r'formatting.*markdown|applying.*formatting|markdown.*formatting', '✨ Formatting Markdown'),
        (r'markdown.*complete|conversion.*complete|rendering.*complete', '✅ Markdown conversion completed'),
        
        # OCR and text operations
        (r'running.*ocr|performing.*ocr|ocr.*detection|executing.*ocr', '🔍 Running OCR detection'),
        (r'detecting.*text.*blocks|identifying.*text|text.*detection|block.*detection', '🔍 Detecting text blocks'),
        (r'extracting.*text.*blocks|reading.*text|text.*extraction|block.*extraction', '📝 Extracting text blocks'),
        (r'extracting.*text|ocr.*text|text.*extraction', '📝 Extracting text'),
        
        # Layout and structure operations
        (r'analyzing.*layout|detecting.*layout|layout.*analysis|layout.*detection', '🔍 Analyzing document layout'),
        (r'processing.*table|table.*processing|detecting.*table|table.*detection', '📊 Processing tables and formatting'),
        (r'finalizing.*table|table.*finalize|structure.*finalize|finalize.*table', '📊 Finalizing table structures'),
        (r'building.*structure|structure.*build|json.*structure|build.*structure', '🏗️ Building structure'),
        
        # Image operations
        (r'processing.*images|detecting.*images|image.*processing|image.*detection', '🖼️ Processing images'),
        (r'extracting.*image|image.*extraction|processing.*image|extract.*image', '🖼️ Extracting embedded images'),
        
        # Model and initialization
        (r'initializing.*model|loading.*model|model.*init|model.*load', '🤖 Initializing AI models for text detection'),
        
        # File operations
        (r'loading.*pdf|reading.*pdf|opening.*pdf|load.*pdf', '📄 Loading PDF pages'),
        
        # Generic fallback patterns (less specific, should be last)
        (r'processing.*document|document.*processing', '🔄 Processing document'),
        (r'analyzing.*document|document.*analysis', '🔍 Analyzing document'),
    ]
    
    def __init__(self, step_callback: Optional[Callable] = None, step_name: str = None, event_loop=None):
        """
        Initialize the Marker log handler.
        
        Args:
            step_callback: Optional async callback function to send step updates
            step_name: Deprecated - no longer used (kept for compatibility)
            event_loop: Optional asyncio event loop for thread-safe callback execution
        """
        super().__init__()
        self.step_callback = step_callback
        self.event_loop = event_loop
        self.seen_steps = set()  # Track already sent steps to avoid duplicates
        self.log_queue = Queue()  # Queue for thread-safe log processing
        self.step_start_times = {}  # Track start times for steps
        
    def emit(self, record: logging.LogRecord) -> None:
        """
        Process a log record from Marker.
        This is called from Marker's thread, so we need to use thread-safe async execution.
        
        This handler intercepts Marker's internal logs during rendering and converts them
        to progress sub-steps. The logs are captured in real-time as Marker processes
        the PDF, allowing us to show detailed progress during the "Rendering Markdown output" step.
        """
        try:
            # Only process Marker-related logs
            if 'marker' not in record.name.lower():
                return
            
            # Extract log message
            log_message = self.format(record)
            
            # Skip very verbose logs (like individual character processing)
            if len(log_message) > 200:
                return
            
            # Debug: log all Marker messages to help identify patterns
            # Enable this temporarily to see what Marker actually logs
            # Set environment variable MARKER_DEBUG_LOGS=1 to enable
            import os
            if os.getenv('MARKER_DEBUG_LOGS') == '1':
                print(f"[MARKER LOG] {record.levelname}: {record.name}: {log_message[:150]}")
            
            # Check if this log matches any step pattern
            matched = False
            for pattern, step_description in self.STEP_PATTERNS:
                if re.search(pattern, log_message, re.IGNORECASE):
                    matched = True
                    # For page-specific logs, extract page number if available
                    page_match = re.search(r'page\s+(\d+)|page\s*:\s*(\d+)|page\s*=\s*(\d+)', log_message, re.IGNORECASE)
                    if page_match:
                        page_num = page_match.group(1) or page_match.group(2) or page_match.group(3)
                        if 'Processing page' in step_description or 'page' in step_description.lower():
                            step_description = f'📄 Processing page {page_num}'
                    
                    # Avoid sending duplicate steps (but allow page-specific ones)
                    step_key = step_description if 'page' not in step_description else f"{step_description}_{time.time()}"
                    if step_key not in self.seen_steps:
                        self.seen_steps.add(step_key)
                        if self.step_callback and self.event_loop:
                            # Send step update using thread-safe coroutine execution
                            # Steps are now main steps, not sub-steps
                            try:
                                step_start_time = time.time()
                                self.step_start_times[step_description] = step_start_time
                                asyncio.run_coroutine_threadsafe(
                                    self._send_step_update(step_description, "in_progress", step_start_time),
                                    self.event_loop
                                )
                            except Exception:
                                pass  # Silently ignore errors to avoid breaking Marker
                    break
            
            # If no pattern matched but it's a DEBUG/INFO level log from renderers/converters,
            # try to extract useful information for progress tracking
            if not matched and record.levelno <= logging.INFO:
                # Focus on logs from renderers and converters (where the actual work happens)
                logger_name_lower = record.name.lower()
                is_relevant_logger = any(x in logger_name_lower for x in ['renderer', 'converter', 'processor', 'ocr'])
                
                if is_relevant_logger:
                    # Look for common progress indicators in Marker logs
                    progress_keywords = ['rendering', 'converting', 'processing', 'extracting', 'detecting', 
                                       'analyzing', 'initializing', 'loading', 'reading', 'writing', 'building',
                                       'formatting', 'parsing', 'identifying', 'recognizing']
                    
                    if any(keyword in log_message.lower() for keyword in progress_keywords):
                        # Try to create a generic progress step from the log message
                        # Extract key action words and object
                        action_match = re.search(
                            r'(rendering|converting|processing|extracting|detecting|analyzing|initializing|loading|reading|writing|building|formatting|parsing|identifying|recognizing)\s+([^,\.:;]+)',
                            log_message, 
                            re.IGNORECASE
                        )
                        if action_match:
                            action = action_match.group(1).capitalize()
                            target = action_match.group(2).strip()
                            # Clean up target (remove extra whitespace, limit length)
                            target = ' '.join(target.split())[:40]
                            # Create a generic step description
                            step_description = f'🔄 {action} {target}'
                            step_key = f"{step_description}_{hash(log_message[:50])}"
                            if step_key not in self.seen_steps:
                                self.seen_steps.add(step_key)
                                if self.step_callback and self.event_loop:
                                    try:
                                        step_start_time = time.time()
                                        self.step_start_times[step_description] = step_start_time
                                        asyncio.run_coroutine_threadsafe(
                                            self._send_step_update(step_description, "in_progress", step_start_time),
                                            self.event_loop
                                        )
                                    except Exception:
                                        pass
                    
        except Exception:
            # Silently ignore errors to avoid breaking Marker's execution
            pass
    
    async def _send_step_update(self, step_description: str, status: str = "in_progress", timestamp: float = None):
        """Send step update via callback."""
        if self.step_callback:
            try:
                import time
                if timestamp is None:
                    timestamp = time.time()
                await self.step_callback(step_description, status, timestamp)
            except Exception:
                pass


def setup_marker_log_interception(
    step_callback: Optional[Callable] = None,
    step_name: str = None,
    event_loop=None
) -> MarkerLogHandler:
    """
    Set up logging interception for Marker library.
    
    Args:
        step_callback: Async callback function to receive step updates
        step_name: Name of the parent step
        event_loop: Optional asyncio event loop for thread-safe execution
        
    Returns:
        The configured MarkerLogHandler instance
    """
    # Get Marker logger and all its child loggers
    marker_logger = logging.getLogger('marker')
    marker_logger.setLevel(logging.DEBUG)  # Use DEBUG to capture more details during rendering
    
    # Also get child loggers that Marker might use (more comprehensive list)
    logger_names = [
        'marker.converters', 
        'marker.models', 
        'marker.renderers', 
        'marker.processors',
        'marker.converters.pdf',
        'marker.renderers.markdown',
        'marker.processors.ocr',
        'marker.processors.layout'
    ]
    
    for logger_name in logger_names:
        child_logger = logging.getLogger(logger_name)
        child_logger.setLevel(logging.DEBUG)  # Use DEBUG to capture more details
    
    # Create and add custom handler
    handler = MarkerLogHandler(
        step_callback=step_callback, 
        step_name=step_name,
        event_loop=event_loop
    )
    handler.setLevel(logging.DEBUG)  # Capture DEBUG level logs for more details
    
    # Add handler to Marker logger and child loggers
    marker_logger.addHandler(handler)
    for logger_name in logger_names:
        child_logger = logging.getLogger(logger_name)
        child_logger.addHandler(handler)
    
    return handler


def remove_marker_log_interception(handler: MarkerLogHandler):
    """
    Remove the custom log handler from Marker logger.
    
    Args:
        handler: The MarkerLogHandler instance to remove
    """
    marker_logger = logging.getLogger('marker')
    marker_logger.removeHandler(handler)

