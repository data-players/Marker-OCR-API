#!/usr/bin/env python3
"""
Test script to verify that Metadata Extraction step is removed and Finalization step is not shown.
"""

import requests
import time
import sys
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_steps_grouping():
    """Test that Metadata Extraction step is removed and Finalization step is not shown."""
    print("=" * 80)
    print("Testing that Metadata Extraction step is removed and Finalization step is not shown")
    print("=" * 80)
    
    # 1. Upload PDF
    pdf_path = Path("tests/backend/FullStack/file-to-parse/LECLERC.pdf")
    if not pdf_path.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    print(f"\n📄 Uploading PDF: {pdf_path}")
    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path.name, f, 'application/pdf')}
        response = requests.post(f"{API_BASE_URL}/api/v1/documents/upload", files=files)
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code}")
            return False
        
        file_id = response.json().get('file_id')
        print(f"✅ Upload successful, file_id: {file_id}")
    
    # 2. Process document
    data = {
        'file_id': file_id,
        'output_format': 'markdown',
        'extract_images': 'false',
    }
    
    response = requests.post(f"{API_BASE_URL}/api/v1/documents/process", data=data)
    if response.status_code != 200:
        print(f"❌ Process request failed: {response.status_code}")
        return False
    
    job_id = response.json().get('job_id')
    print(f"✅ Processing started, job_id: {job_id}")
    
    # 3. Wait for completion
    print("\n📊 Waiting for completion...")
    max_polls = 300
    poll_count = 0
    
    while poll_count < max_polls:
        response = requests.get(f"{API_BASE_URL}/api/v1/documents/jobs/{job_id}")
        if response.status_code != 200:
            break
        
        job_status = response.json()
        status = job_status.get('status')
        
        if status == 'completed':
            print(f"\n✅ Processing completed at poll {poll_count}")
            break
        elif status == 'failed':
            print(f"\n❌ Processing failed")
            return False
        
        time.sleep(0.5)
        poll_count += 1
    
    # 4. Check final steps
    response = requests.get(f"{API_BASE_URL}/api/v1/documents/jobs/{job_id}")
    job_status = response.json()
    steps = job_status.get('steps', [])
    
    print(f"\n📊 Final steps ({len(steps)} total):")
    step_names = []
    for step in steps:
        name = step.get('name')
        status = step.get('status')
        duration = step.get('duration')
        duration_str = f" ({duration*1000:.2f}ms)" if duration else ""
        print(f"   - {name} ({status}){duration_str}")
        step_names.append(name)
    
    # 5. Verify steps
    has_metadata_extraction = "Metadata Extraction" in step_names
    has_finalization = "Finalization" in step_names
    
    if has_metadata_extraction:
        print(f"\n❌ ERROR: 'Metadata Extraction' step still exists!")
        return False
    
    if has_finalization:
        print(f"\n❌ ERROR: 'Finalization' step should not be shown!")
        return False
    
    print(f"\n✅ SUCCESS: Steps are correct!")
    print(f"   - 'Metadata Extraction' step removed")
    print(f"   - 'Finalization' step not shown (no utility for output)")
    
    return True

if __name__ == "__main__":
    try:
        success = test_steps_grouping()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

