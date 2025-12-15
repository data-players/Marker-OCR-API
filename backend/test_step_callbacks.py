#!/usr/bin/env python3
"""Test script to verify step callbacks are being called."""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/app')

from app.services.document_parser import DocumentParserService
from app.models.enums import OutputFormat

# Track callbacks
callbacks_received = []

async def test_callback(step_name: str, status: str, timestamp=None):
    """Test callback that logs what it receives."""
    print(f"✅ CALLBACK RECEIVED: step='{step_name}', status='{status}', timestamp={timestamp}")
    callbacks_received.append((step_name, status, timestamp))

async def main():
    print("=" * 80)
    print("TEST: Step callback verification")
    print("=" * 80)
    
    # Create parser
    parser = DocumentParserService()
    
    # Parse a dummy PDF (use any existing PDF)
    test_file = "/app/uploads/9b9d1339-78ff-4a43-95d1-820cbb1a282a.pdf"
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"\n1. Parsing PDF with callback tracking...")
    print(f"   File: {test_file}")
    print("-" * 80)
    
    result = await parser.parse_document(
        file_path=test_file,
        output_format=OutputFormat.MARKDOWN,
        force_ocr=False,
        extract_images=False,
        paginate_output=False,
        language=None,
        step_callback=test_callback
    )
    
    print("-" * 80)
    print(f"\n2. Parsing complete!")
    print(f"   Result type: {type(result)}")
    print(f"   Has content: {result is not None and hasattr(result, 'markdown_content')}")
    
    print(f"\n3. Callbacks received: {len(callbacks_received)}")
    if callbacks_received:
        print("   Steps:")
        for step_name, status, _ in callbacks_received:
            print(f"      - {step_name}: {status}")
    else:
        print("   ❌ NO CALLBACKS RECEIVED!")
    
    print("\n" + "=" * 80)
    print("END OF TEST")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())

