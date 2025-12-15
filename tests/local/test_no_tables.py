#!/usr/bin/env python3
"""
Test script to verify that table-related steps are not shown when extract_tables=False.
"""

import requests
import time
import sys
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_no_tables():
    """Test that table-related steps are not shown when extract_tables=False."""
    print("=" * 80)
    print("Testing that table-related steps are NOT shown when extract_tables=False")
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
    
    # 2. Process document with paginate_output=False
    data = {
        'file_id': file_id,
        'output_format': 'markdown',
        'extract_images': 'false',
        'paginate_output': 'false',  # Explicitly set to False
    }
    
    response = requests.post(f"{API_BASE_URL}/api/v1/documents/process", data=data)
    if response.status_code != 200:
        print(f"❌ Process request failed: {response.status_code}")
        return False
    
    job_id = response.json().get('job_id')
    print(f"✅ Processing started, job_id: {job_id}")
    print(f"   Options: extract_tables=False")
    
    # 3. Check initial state
    print("\n📊 Checking initial state...")
    time.sleep(0.5)
    
    response = requests.get(f"{API_BASE_URL}/api/v1/documents/jobs/{job_id}")
    if response.status_code != 200:
        print(f"❌ Status check failed: {response.status_code}")
        return False
    
    job_status = response.json()
    steps = job_status.get('steps', [])
    ocr_step = None
    for step in steps:
        if step.get('name') == 'OCR Processing':
            ocr_step = step
            break
    
    if not ocr_step:
        print("❌ OCR Processing step not found")
        return False
    
    initial_sub_steps = ocr_step.get('sub_steps_detailed', [])
    initial_sub_step_names = [s.get('name') for s in initial_sub_steps]
    
    print(f"\n✅ Initial state: {len(initial_sub_step_names)} sub-steps")
    table_steps_in_initial = [name for name in initial_sub_step_names if 'table' in name.lower() or '📊 Recognizing tables' in name]
    if table_steps_in_initial:
        print(f"❌ ERROR: Table-related steps found in initial state: {table_steps_in_initial}")
        return False
    
    # 4. Wait for completion
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
    
    # 5. Check final state
    response = requests.get(f"{API_BASE_URL}/api/v1/documents/jobs/{job_id}")
    job_status = response.json()
    steps = job_status.get('steps', [])
    ocr_step = None
    for step in steps:
        if step.get('name') == 'OCR Processing':
            ocr_step = step
            break
    
    final_sub_steps = ocr_step.get('sub_steps_detailed', [])
    final_sub_step_names = [s.get('name') for s in final_sub_steps]
    
    print(f"\n✅ Final state: {len(final_sub_step_names)} sub-steps")
    table_steps_in_final = [name for name in final_sub_step_names if 'table' in name.lower() or '📊 Recognizing tables' in name]
    if table_steps_in_final:
        print(f"❌ ERROR: Table-related steps found in final state: {table_steps_in_final}")
        print(f"   All sub-steps: {final_sub_step_names}")
        return False
    
    print(f"\n✅ SUCCESS: No table-related steps found when extract_tables=False!")
    return True

if __name__ == "__main__":
    try:
        success = test_no_tables()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

