"""
Document parsing service using the Marker library.
Handles PDF to JSON/Markdown conversion with different processing options.
"""

import asyncio
import json
import time
import os
import gc
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from concurrent.futures import ThreadPoolExecutor
import re

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
from app.models.enums import ProcessingOptions, OutputFormat

logger = get_logger(__name__)


def convert_pil_images(data):
    """Convert PIL Image objects to dictionaries for Pydantic serialization."""
    if hasattr(data, 'size'):  # PIL Image object
        return {
            "width": data.size[0] if hasattr(data, 'size') else None,
            "height": data.size[1] if hasattr(data, 'size') else None,
            "format": getattr(data, 'format', 'unknown'),
            "mode": getattr(data, 'mode', 'unknown')
        }
    elif isinstance(data, dict):
        return {k: convert_pil_images(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_pil_images(item) for item in data]
    else:
        return data


def create_rich_structure_from_markdown(markdown_text: str, images: dict, metadata: any) -> dict:
    """
    Create a rich document structure similar to datalab.to from Marker's markdown output.
    This analyzes the markdown and creates blocks with types and hierarchy.
    """
    try:
        blocks = []
        block_id = 0
        
        # Convert PIL Images to dictionary format for processing
        processed_images = {}
        if isinstance(images, dict):
            for key, value in images.items():
                if hasattr(value, 'size'):  # PIL Image object
                    processed_images[key] = {
                        "width": value.size[0] if hasattr(value, 'size') else 100,
                        "height": value.size[1] if hasattr(value, 'size') else 100,
                        "format": getattr(value, 'format', 'unknown')
                    }
                else:
                    processed_images[key] = value
        
        # Split markdown into lines and analyze
        lines = markdown_text.split('\n')
        current_section_hierarchy = {}
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            block_id += 1
            
            # Detect different block types
            if line.startswith('![]('):
                # Image block
                image_match = re.search(r'!\[\]\(([^)]+)\)', line)
                if image_match:
                    image_name = image_match.group(1)
                    image_info = processed_images.get(image_name, {})
                    blocks.append({
                        "block_type": "Picture",
                        "id": f"/page/0/Picture/{block_id}",
                        "html": f'<img src="{image_name}" />',
                        "images": {image_name: image_info} if image_info else {},
                        "bbox": [0, 0, image_info.get('width', 100), image_info.get('height', 100)] if image_info else [0, 0, 100, 100],
                        "section_hierarchy": current_section_hierarchy.copy()
                    })
                    
            elif line.startswith('## '):
                # Section header
                header_text = line[3:].strip()
                current_section_hierarchy['2'] = f"/page/0/SectionHeader/{block_id}"
                blocks.append({
                    "block_type": "SectionHeader", 
                    "id": f"/page/0/SectionHeader/{block_id}",
                    "html": f"<h2>{header_text}</h2>",
                    "images": {},
                    "bbox": [0, 0, 500, 30],
                    "section_hierarchy": current_section_hierarchy.copy()
                })
                
            elif line.startswith('# '):
                # Main header
                header_text = line[2:].strip()
                current_section_hierarchy['1'] = f"/page/0/Header/{block_id}"
                blocks.append({
                    "block_type": "Header",
                    "id": f"/page/0/Header/{block_id}",
                    "html": f"<h1>{header_text}</h1>", 
                    "images": {},
                    "bbox": [0, 0, 500, 40],
                    "section_hierarchy": current_section_hierarchy.copy()
                })
                
            elif line.startswith('|') and '|' in line[1:]:
                # Table - collect consecutive table lines
                table_lines = [line]
                j = i + 1
                while j < len(lines) and lines[j].strip().startswith('|'):
                    table_lines.append(lines[j].strip())
                    j += 1
                
                # Create table structure
                table_html = "<table><tbody>"
                for table_line in table_lines:
                    if '---' in table_line:  # Skip separator line
                        continue
                    cells = [cell.strip() for cell in table_line.split('|')[1:-1]]
                    table_html += "<tr>"
                    for cell in cells:
                        table_html += f"<td>{cell}</td>"
                    table_html += "</tr>"
                table_html += "</tbody></table>"
                
                blocks.append({
                    "block_type": "Table",
                    "id": f"/page/0/Table/{block_id}",
                    "html": table_html,
                    "images": {},
                    "bbox": [0, 0, 600, len(table_lines) * 25],
                    "section_hierarchy": current_section_hierarchy.copy(),
                    "children": []  # Could add individual cells here
                })
                
            elif line and not line.startswith('#') and not line.startswith('!['):
                # Regular text block
                blocks.append({
                    "block_type": "Text",
                    "id": f"/page/0/Text/{block_id}",
                    "html": f'<p block-type="Text">{line}</p>',
                    "images": {},
                    "bbox": [0, 0, 500, 20],
                    "section_hierarchy": current_section_hierarchy.copy()
                })
        
        # Create document structure
        document_structure = {
            "block_type": "Document",
            "children": [{
                "block_type": "Page",
                "id": "/page/0/Page/0",
                "bbox": [0, 0, 596, 842],  # A4 size
                "children": blocks,
                "section_hierarchy": {}
            }]
        }
        
        logger.info(f"Created rich structure with {len(blocks)} blocks")
        return document_structure
        
    except Exception as e:
        logger.error(f"Failed to create rich structure: {str(e)}")
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
        processing_options: ProcessingOptions, 
        output_format: OutputFormat
    ) -> Dict[str, Any]:
        """
        Parse a document using Marker.
        
        Args:
            file_path: Path to the PDF file
            processing_options: Processing options enum
            output_format: Output format enum
            
        Returns:
            Dictionary containing parsed content and metadata
        """
        if not self.models_ready:
            if not await self.initialize_models():
                raise RuntimeError(f"Marker processing failed: {self.model_load_error}")
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting document parsing: {file_path}")
            
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Process document in thread pool
            loop = asyncio.get_event_loop()
            
            def _process_document():
                try:
                    # ✨ GÉNÉRATION DES DEUX FORMATS SIMULTANÉMENT ✨
                    results = {}
                    
                    # 1. Générer le format JSON natif (structure riche)
                    logger.info("🎯 Generating native JSON format...")
                    json_config = {"output_format": "json"}
                    json_config_parser = ConfigParser(json_config)
                    
                    json_converter = PdfConverter(
                        config=json_config_parser.generate_config_dict(),
                        artifact_dict=self.models_dict,
                        processor_list=json_config_parser.get_processors(),
                        renderer=json_config_parser.get_renderer()
                    )
                    
                    json_rendered = json_converter(file_path)
                    
                    # Extraire la structure JSON native
                    if hasattr(json_rendered, 'children') and hasattr(json_rendered, 'block_type'):
                        rich_structure = {
                            "block_type": json_rendered.block_type,
                            "id": getattr(json_rendered, 'id', '/document/0'),
                            "children": json_rendered.children,
                        }
                        logger.info(f"✅ JSON native: {json_rendered.block_type} with {len(json_rendered.children) if hasattr(json_rendered, 'children') else 0} children")
                    else:
                        rich_structure = None
                        logger.warning("⚠️ JSON structure not as expected")
                    
                    # 2. Générer le format Markdown pour la preview
                    logger.info("📝 Generating markdown format...")
                    markdown_config = {"output_format": "markdown"}
                    markdown_config_parser = ConfigParser(markdown_config)
                    
                    markdown_converter = PdfConverter(
                        config=markdown_config_parser.generate_config_dict(),
                        artifact_dict=self.models_dict,
                        processor_list=markdown_config_parser.get_processors(),
                        renderer=markdown_config_parser.get_renderer()
                    )
                    
                    markdown_rendered = markdown_converter(file_path)
                    
                    # Extraire le contenu markdown
                    if hasattr(markdown_rendered, 'markdown'):
                        markdown_content = markdown_rendered.markdown
                        logger.info(f"✅ Markdown: {len(markdown_content)} characters")
                    else:
                        # Fallback avec text_from_rendered
                        markdown_content, _, _ = text_from_rendered(markdown_rendered)
                        logger.info("✅ Markdown via text_from_rendered fallback")
                    
                    # 3. Récupérer les métadonnées et images (du JSON ou markdown)
                    metadata = getattr(json_rendered, 'metadata', getattr(markdown_rendered, 'metadata', {}))
                    images = getattr(json_rendered, 'images', getattr(markdown_rendered, 'images', {}))
                    
                    # 🔧 Convertir les objets PIL Image pour la sérialisation
                    images = convert_pil_images(images)
                    metadata = convert_pil_images(metadata)
                    
                    logger.info("🎉 Successfully generated BOTH formats!")
                    
                    # Prepare result before cleanup
                    result = {
                        "text": markdown_content,  # Contenu markdown pour preview
                        "markdown_content": markdown_content,  # Contenu markdown explicite
                        "rich_structure": rich_structure,  # Structure JSON native
                        "metadata": metadata,
                        "images": images,
                        "processing_time": None  # Will be set below
                    }
                    
                    # 🧹 Force garbage collection to free memory
                    del json_converter, markdown_converter, json_rendered, markdown_rendered
                    gc.collect()
                    logger.info("🧹 Memory cleanup completed")
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Dual format processing failed, trying fallback: {str(e)}")
                    
                    # Fallback vers une seule méthode si nécessaire
                    try:
                        converter = PdfConverter(artifact_dict=self.models_dict)
                        rendered = converter(file_path)
                        text, metadata, images = text_from_rendered(rendered)
                        rich_structure = create_rich_structure_from_markdown(text, images, metadata)
                        
                        result = {
                            "text": text,
                            "markdown_content": text,
                            "rich_structure": rich_structure,
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