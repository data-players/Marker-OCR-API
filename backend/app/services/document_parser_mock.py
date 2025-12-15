"""
Mock document parsing service for testing without Marker library.
Provides a lightweight implementation for testing core functionality.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from app.core.logger import LoggerMixin
from app.core.config import settings
from app.core.exceptions import (
    MarkerProcessingError,
    FileNotFoundError as CustomFileNotFoundError,
    FileProcessingError
)
from app.models.request_models import OutputFormat


class MockDocumentParserService(LoggerMixin):
    """Mock service for testing document parsing without heavy dependencies."""
    
    def __init__(self):
        self._models_loaded = True  # Always "loaded" in mock
        self._models = "mock_models"
    
    async def initialize(self) -> None:
        """Mock initialization - always succeeds quickly."""
        self.log_operation("Mock Marker models loaded")
        await asyncio.sleep(0.1)  # Simulate quick loading
    
    async def process_document(
        self,
        file_path: Path,
        output_format: OutputFormat,
        force_ocr: bool = False,
        extract_images: bool = False,
        extract_tables: bool = True,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mock document processing that returns realistic test data.
        """
        if not file_path.exists():
            raise CustomFileNotFoundError(str(file_path))
        
        await self.initialize()
        
        self.log_operation(
            "Mock document processing started",
            file_path=str(file_path),
            output_format=output_format.value
        )
        
        start_time = time.time()
        
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        processing_time = time.time() - start_time
        
        # Generate mock result based on file
        mock_result = self._generate_mock_result(
            file_path, output_format, processing_time, extract_images, extract_tables
        )
        
        self.log_performance(
            "Mock document processing", 
            processing_time,
            pages=mock_result.get("page_count", 1)
        )
        
        return mock_result
    
    def _generate_mock_result(
        self,
        file_path: Path,
        output_format: OutputFormat,
        processing_time: float,
        extract_images: bool,
        extract_tables: bool
    ) -> Dict[str, Any]:
        """Generate realistic mock processing result."""
        
        filename = file_path.stem
        
        # Mock text content based on filename
        if "invoice" in filename.lower():
            mock_text = self._get_mock_invoice_text()
        elif "report" in filename.lower():
            mock_text = self._get_mock_report_text()
        else:
            mock_text = self._get_mock_generic_text(filename)
        
        result = {
            "processing_time": processing_time,
            "metadata": {
                "page_count": 2,
                "title": f"Mock Document: {filename}",
                "author": "Test Author",
                "creation_date": "2024-01-01",
                "file_size": file_path.stat().st_size if file_path.exists() else 1000
            },
            "page_count": 2,
            "images": ["mock_image_1.png", "mock_image_2.png"] if extract_images else [],
            "tables": [
                {
                    "page": 1,
                    "data": [["Header 1", "Header 2"], ["Value 1", "Value 2"]],
                    "html": "<table><tr><th>Header 1</th><th>Header 2</th></tr><tr><td>Value 1</td><td>Value 2</td></tr></table>"
                }
            ] if extract_tables else [],
        }
        
        if output_format in [OutputFormat.JSON, OutputFormat.BOTH]:
            result["json_content"] = {
                "text": mock_text,
                "structure": self._extract_mock_structure(mock_text),
                "metadata": result["metadata"]
            }
        
        if output_format in [OutputFormat.MARKDOWN, OutputFormat.BOTH]:
            result["markdown_content"] = self._convert_to_markdown(mock_text)
        
        return result
    
    def _get_mock_invoice_text(self) -> str:
        """Generate mock invoice text."""
        return """INVOICE #INV-2024-001

Bill To:
John Doe
123 Main Street
Anytown, ST 12345

Date: January 1, 2024
Due Date: January 31, 2024

Description                Qty    Rate     Amount
Web Development Service    1      $1000    $1000.00
Hosting Setup             1      $200     $200.00

Subtotal:                                  $1200.00
Tax (8%):                                  $96.00
Total:                                     $1296.00

Payment Terms: Net 30 days
Thank you for your business!"""
    
    def _get_mock_report_text(self) -> str:
        """Generate mock report text."""
        return """QUARTERLY REPORT Q1 2024

Executive Summary

This report presents the key findings and performance metrics for the first quarter of 2024. 
Our organization has achieved significant milestones and continues to grow steadily.

Key Metrics:
- Revenue: $2.5M (15% increase)
- Customer Growth: 25% quarter-over-quarter
- Market Share: 12% in target segment

Performance Analysis

The first quarter showed strong performance across all major indicators. Customer 
acquisition exceeded targets by 20%, while retention rates remained stable at 95%.

Recommendations

1. Continue investment in customer acquisition
2. Expand into new market segments
3. Strengthen product development team

Conclusion

Q1 2024 results demonstrate strong momentum and position us well for continued growth."""
    
    def _get_mock_generic_text(self, filename: str) -> str:
        """Generate generic mock text."""
        return f"""Mock Document: {filename}

This is a mock document generated for testing purposes. The document contains 
multiple paragraphs with various types of content including:

• Bullet points and lists
• Tables with structured data
• Headers and subheaders
• Regular paragraphs with text content

Section 1: Introduction

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor 
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis 
nostrud exercitation ullamco laboris.

Section 2: Main Content

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore 
eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, 
sunt in culpa qui officia deserunt mollit anim id est laborum.

Conclusion

This mock document demonstrates the structure and content that would be 
extracted from a real PDF document using the Marker library."""
    
    def _extract_mock_structure(self, text: str) -> Dict[str, Any]:
        """Extract mock document structure."""
        lines = text.split('\n')
        
        structure = {
            "headings": [],
            "paragraphs": [],
            "tables": [],
            "lists": []
        }
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Detect headings (lines in ALL CAPS or ending with :)
            if line.isupper() or line.endswith(':'):
                structure["headings"].append({
                    "level": 1 if line.isupper() else 2,
                    "text": line.rstrip(':'),
                    "line_number": i
                })
            # Detect list items
            elif line.startswith(('•', '-', '*', '1.', '2.', '3.')):
                structure["lists"].append({
                    "text": line[2:].strip() if line.startswith(('•', '-', '*')) else line[3:].strip(),
                    "line_number": i
                })
            # Regular paragraphs
            elif len(line) > 20:
                structure["paragraphs"].append({
                    "text": line,
                    "line_number": i
                })
        
        return structure
    
    def _convert_to_markdown(self, text: str) -> str:
        """Convert mock text to markdown format."""
        lines = text.split('\n')
        markdown_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                markdown_lines.append('')
                continue
            
            # Convert headings
            if line.isupper():
                markdown_lines.append(f"# {line}")
            elif line.endswith(':'):
                markdown_lines.append(f"## {line.rstrip(':')}")
            # Convert list items
            elif line.startswith('•'):
                markdown_lines.append(f"- {line[1:].strip()}")
            elif line.startswith(('-', '*')):
                markdown_lines.append(f"- {line[1:].strip()}")
            # Regular text
            else:
                markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)
    
    async def get_supported_formats(self) -> List[str]:
        """Get list of supported input formats."""
        return [".pdf", ".txt", ".md"]  # Mock supports more formats
    
    async def cleanup(self) -> None:
        """Mock cleanup - always succeeds."""
        self.log_operation("Mock document parser service cleaned up") 