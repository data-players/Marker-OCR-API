#!/usr/bin/env python3
"""
Test script to process a PDF and observe Marker logs.
This helps identify what logs Marker generates during rendering.
Run this inside the Docker container.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add app to path
sys.path.insert(0, '/app')

from app.services.document_parser import DocumentParserService
from app.models.enums import OutputFormat

async def test_marker_logs():
    """Test Marker log capture with example PDF."""
    print("=" * 80)
    print("Testing Marker log capture")
    print("=" * 80)
    
    # Enable debug logging
    os.environ['MARKER_DEBUG_LOGS'] = '1'
    
    # Try multiple possible paths
    pdf_paths = [
        "/app/uploads/exemple_facture.pdf",
        "/app/../tests/backend/FullStack/file-to-parse/exemple_facture.pdf",
        "/app/tests/backend/FullStack/file-to-parse/exemple_facture.pdf",
    ]
    
    pdf_path = None
    for path in pdf_paths:
        if os.path.exists(path):
            pdf_path = path
            break
    
    if not pdf_path:
        print(f"❌ PDF file not found in any of these locations:")
        for path in pdf_paths:
            print(f"   - {path}")
        return
    
    print(f"📄 Processing: {pdf_path}")
    print("-" * 80)
    
    # Track sub-steps
    sub_steps_seen = []
    
    async def step_callback(step_name: str, status: str, timestamp_or_substep=None):
        """Callback to track step updates."""
        if status == "sub_step":
            if isinstance(timestamp_or_substep, str):
                sub_step_name = timestamp_or_substep
                if sub_step_name not in sub_steps_seen:
                    sub_steps_seen.append(sub_step_name)
                    print(f"✅ Sub-step detected: {sub_step_name}")
            elif isinstance(timestamp_or_substep, tuple):
                sub_step_name, end_time = timestamp_or_substep
                print(f"✅ Sub-step completed: {sub_step_name} at {end_time}")
        else:
            print(f"📊 Step: {step_name} -> {status}")
    
    parser = DocumentParserService()
    
    try:
        result = await parser.parse_document(
            file_path=pdf_path,
            output_format=OutputFormat.MARKDOWN,
            force_ocr=False,
            extract_images=False,
            step_callback=step_callback
        )
        
        print("-" * 80)
        print("✅ Processing completed!")
        print(f"📝 Sub-steps captured: {len(sub_steps_seen)}")
        for i, step in enumerate(sub_steps_seen, 1):
            print(f"  {i}. {step}")
        
        if result.get('markdown'):
            print(f"📄 Markdown length: {len(result['markdown'])} characters")
            print(f"📄 First 200 chars: {result['markdown'][:200]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_marker_logs())


