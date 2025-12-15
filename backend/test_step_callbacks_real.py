#!/usr/bin/env python3
"""
Test script to verify step callbacks are being called during real Marker processing.
This test uses the FullStack environment with models loaded.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, '/app')

from app.services.document_parser import DocumentParserService
from app.models.enums import OutputFormat

# Track callbacks
callbacks_received = []
callback_details = []

async def test_callback(step_name: str, status: str, timestamp=None):
    """Test callback that logs what it receives."""
    msg = f"✅ CALLBACK: step='{step_name}', status='{status}', timestamp={timestamp}"
    print(msg)
    callbacks_received.append((step_name, status, timestamp))
    callback_details.append(msg)

async def main():
    print("=" * 80)
    print("TEST: Step callback verification with real Marker processing")
    print("=" * 80)
    
    # Test file - use any existing PDF in uploads
    test_file = None
    upload_dir = "/app/uploads"
    if os.path.exists(upload_dir):
        for file in os.listdir(upload_dir):
            if file.endswith('.pdf'):
                test_file = os.path.join(upload_dir, file)
                break
    
    if not test_file or not os.path.exists(test_file):
        print(f"❌ No PDF test file found in {upload_dir}!")
        return
    
    print(f"\n1. Test file: {test_file}")
    print(f"   File exists: {os.path.exists(test_file)}")
    print(f"   File size: {os.path.getsize(test_file)} bytes")
    
    # Create parser
    parser = DocumentParserService()
    
    print(f"\n2. Parser created")
    print(f"   Models ready (before init): {parser.models_ready}")
    
    # Initialize models
    print(f"\n3. Initializing Marker models...")
    await parser.initialize_models()
    
    print(f"   Models ready (after init): {parser.models_ready}")
    print(f"   Models dict: {parser.models_dict is not None}")
    
    if not parser.models_ready:
        print(f"   ❌ Failed to load models: {parser.model_load_error}")
        return
    
    print(f"\n4. Starting document parsing with callback tracking...")
    print("-" * 80)
    
    try:
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
        print(f"\n5. Parsing complete!")
        print(f"   Result type: {type(result)}")
        print(f"   Has markdown_content: {result is not None and hasattr(result, 'markdown_content')}")
        if result and hasattr(result, 'markdown_content'):
            print(f"   Content length: {len(result.markdown_content)} chars")
        
        print(f"\n6. Callbacks received: {len(callbacks_received)}")
        if callbacks_received:
            print("   📊 Callback timeline:")
            for i, (step_name, status, ts) in enumerate(callbacks_received, 1):
                print(f"      {i}. [{status:12}] {step_name}")
        else:
            print("   ❌ NO CALLBACKS RECEIVED!")
            print("\n   This confirms the bug: callbacks are not being sent.")
        
        print("\n6. Detailed callback log:")
        for detail in callback_details:
            print(f"   {detail}")
            
    except Exception as e:
        print(f"\n❌ ERROR during parsing: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("END OF TEST")
    print("=" * 80)
    
    # Return exit code based on results
    if callbacks_received:
        print("\n✅ SUCCESS: Callbacks are working!")
        return 0
    else:
        print("\n❌ FAILURE: No callbacks received (bug confirmed)")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

