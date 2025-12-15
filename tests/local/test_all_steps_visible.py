#!/usr/bin/env python3
"""
Test script to verify that all steps are visible from the start and remain visible.
"""

import requests
import time
import sys
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_all_steps_visible():
    """Test that all steps are visible from the start."""
    print("=" * 80)
    print("Testing that all steps are visible from the start")
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
    
    # 3. Check initial state (should have all steps)
    print("\n📊 Checking initial state...")
    time.sleep(0.5)  # Wait a bit for initial state
    
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
    print("   Sub-steps:")
    for i, name in enumerate(initial_sub_step_names, 1):
        status = initial_sub_steps[i-1].get('status', 'unknown')
        print(f"     {i}. {name} ({status})")
    
    # 4. Poll until completion and verify consistency
    print("\n📊 Polling until completion...")
    max_polls = 300
    poll_count = 0
    
    while poll_count < max_polls:
        response = requests.get(f"{API_BASE_URL}/api/v1/documents/jobs/{job_id}")
        if response.status_code != 200:
            break
        
        job_status = response.json()
        status = job_status.get('status')
        
        steps = job_status.get('steps', [])
        ocr_step = None
        for step in steps:
            if step.get('name') == 'OCR Processing':
                ocr_step = step
                break
        
        if ocr_step:
            current_sub_steps = ocr_step.get('sub_steps_detailed', [])
            current_sub_step_names = [s.get('name') for s in current_sub_steps]
            
            # Check if any step disappeared
            missing_steps = set(initial_sub_step_names) - set(current_sub_step_names)
            if missing_steps:
                print(f"\n❌ ERROR at poll {poll_count}: Steps disappeared!")
                print(f"   Missing: {missing_steps}")
                return False
        
        if status == 'completed':
            print(f"\n✅ Processing completed at poll {poll_count}")
            break
        elif status == 'failed':
            print(f"\n❌ Processing failed")
            return False
        
        time.sleep(0.5)
        poll_count += 1
    
    # 5. Verify final state
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
    print("   Sub-steps:")
    for i, name in enumerate(final_sub_step_names, 1):
        status = final_sub_steps[i-1].get('status', 'unknown')
        duration = final_sub_steps[i-1].get('duration')
        duration_str = f" ({duration*1000:.2f}ms)" if duration else ""
        print(f"     {i}. {name} ({status}){duration_str}")
    
    # 6. Verify all initial steps are still present
    missing_in_final = set(initial_sub_step_names) - set(final_sub_step_names)
    if missing_in_final:
        print(f"\n❌ ERROR: Some steps disappeared in final state!")
        print(f"   Missing: {missing_in_final}")
        return False
    
    print(f"\n✅ SUCCESS: All {len(initial_sub_step_names)} steps remained visible throughout processing!")
    return True

if __name__ == "__main__":
    try:
        success = test_all_steps_visible()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

