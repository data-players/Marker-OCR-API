#!/usr/bin/env python3
"""
Test script to verify that sub-steps are correctly returned via the API
and can be displayed in the frontend.
"""

import requests
import time
import json
import sys
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_substeps_api():
    """Test that sub-steps are correctly returned via the API."""
    print("=" * 80)
    print("Testing API sub-steps tracking")
    print("=" * 80)
    
    # 1. Upload a PDF file
    pdf_path = Path("tests/backend/FullStack/file-to-parse/exemple_facture.pdf")
    if not pdf_path.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    print(f"\n📄 Uploading PDF: {pdf_path}")
    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path.name, f, 'application/pdf')}
        
        response = requests.post(f"{API_BASE_URL}/api/v1/documents/upload", files=files)
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code}")
            print(response.text)
            return False
        
        upload_result = response.json()
        file_id = upload_result.get('file_id')
        print(f"✅ Upload successful, file_id: {file_id}")
    
    # 2. Process the document
    print(f"\n🔄 Processing document...")
    data = {
        'file_id': file_id,
        'output_format': 'markdown',
        'extract_images': 'false',
    }
    
    response = requests.post(f"{API_BASE_URL}/api/v1/documents/process", data=data)
    if response.status_code != 200:
        print(f"❌ Process request failed: {response.status_code}")
        print(response.text)
        return False
    
    process_result = response.json()
    job_id = process_result.get('job_id')
    print(f"✅ Processing started, job_id: {job_id}")
    
    # 3. Poll job status and track sub-steps
    print("\n📊 Polling job status...")
    print("-" * 80)
    
    seen_substeps = {}
    max_polls = 120  # 60 seconds max (500ms polling)
    poll_count = 0
    
    while poll_count < max_polls:
        response = requests.get(f"{API_BASE_URL}/api/v1/documents/jobs/{job_id}")
        if response.status_code != 200:
            print(f"❌ Status check failed: {response.status_code}")
            break
        
        job_status = response.json()
        status = job_status.get('status')
        
        # Check for steps
        steps = job_status.get('steps', [])
        ocr_step = None
        for step in steps:
            if step.get('name') == 'OCR Processing':
                ocr_step = step
                break
        
        if ocr_step:
            sub_steps_detailed = ocr_step.get('sub_steps_detailed', [])
            
            # Track new sub-steps
            for sub_step in sub_steps_detailed:
                sub_name = sub_step.get('name')
                sub_status = sub_step.get('status')
                sub_duration = sub_step.get('duration')
                
                if sub_name not in seen_substeps:
                    seen_substeps[sub_name] = {
                        'status': sub_status,
                        'duration': sub_duration,
                        'first_seen': time.time()
                    }
                    print(f"✅ New sub-step detected: {sub_name} ({sub_status})")
                elif seen_substeps[sub_name]['status'] != sub_status:
                    old_status = seen_substeps[sub_name]['status']
                    seen_substeps[sub_name]['status'] = sub_status
                    if sub_duration:
                        seen_substeps[sub_name]['duration'] = sub_duration
                    print(f"🔄 Sub-step updated: {sub_name} ({old_status} -> {sub_status})")
                    if sub_duration:
                        print(f"   Duration: {sub_duration:.3f}s")
        
        # Show current status
        if status == 'completed':
            print("\n" + "=" * 80)
            print("✅ Processing completed!")
            print("=" * 80)
            break
        elif status == 'failed':
            print(f"\n❌ Processing failed: {job_status.get('error_message', 'Unknown error')}")
            break
        
        time.sleep(0.5)  # Poll every 500ms
        poll_count += 1
    
    # 3. Summary
    print("\n" + "=" * 80)
    print("📝 Sub-steps Summary")
    print("=" * 80)
    print(f"Total sub-steps captured: {len(seen_substeps)}")
    print("\nSub-steps in order:")
    for i, (name, info) in enumerate(seen_substeps.items(), 1):
        duration_str = f" ({info['duration']:.3f}s)" if info.get('duration') else ""
        print(f"  {i}. {name} - {info['status']}{duration_str}")
    
    # 4. Verify expected sub-steps
    expected_substeps = [
        "📄 Loading PDF pages",
        "🔍 Analyzing document layout",
        "🤖 Initializing AI models for text detection",
        "📝 Extracting text for Markdown",
        "📊 Processing tables and formatting",
        "🎨 Rendering Markdown output",
        "🔍 Recognizing document layout",  # From tqdm interception
        "🔍 Running OCR error detection",   # From tqdm interception
        "📊 Recognizing tables",            # From tqdm interception
    ]
    
    print("\n" + "=" * 80)
    print("🔍 Verification")
    print("=" * 80)
    
    found_expected = []
    missing_expected = []
    
    for expected in expected_substeps:
        if expected in seen_substeps:
            found_expected.append(expected)
        else:
            missing_expected.append(expected)
    
    print(f"✅ Found {len(found_expected)}/{len(expected_substeps)} expected sub-steps")
    if missing_expected:
        print(f"⚠️  Missing {len(missing_expected)} expected sub-steps:")
        for missing in missing_expected:
            print(f"   - {missing}")
    
    # Check if we have the detailed tqdm sub-steps
    tqdm_substeps = [
        "🔍 Recognizing document layout",
        "🔍 Running OCR error detection",
        "📊 Recognizing tables",
    ]
    
    tqdm_found = [s for s in tqdm_substeps if s in seen_substeps]
    print(f"\n🎯 Tqdm-intercepted sub-steps: {len(tqdm_found)}/{len(tqdm_substeps)}")
    if tqdm_found:
        print("   ✅ Tqdm interception is working!")
    else:
        print("   ⚠️  Tqdm interception may not be working")
    
    return len(found_expected) >= 6  # At least 6 basic sub-steps should be found

if __name__ == "__main__":
    try:
        success = test_substeps_api()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

