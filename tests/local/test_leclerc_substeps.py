#!/usr/bin/env python3
"""
Test script to verify sub-steps timing with LECLERC.pdf
"""

import requests
import time
import sys
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_leclerc_substeps():
    """Test sub-steps timing with LECLERC.pdf."""
    print("=" * 80)
    print("Testing sub-steps timing with LECLERC.pdf")
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
            print(response.text)
            return False
        
        upload_result = response.json()
        file_id = upload_result.get('file_id')
        print(f"✅ Upload successful, file_id: {file_id}")
    
    # 2. Process document
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
    
    # 3. Poll job status and track sub-steps with timing
    print("\n📊 Polling job status and tracking sub-steps...")
    print("-" * 80)
    
    seen_substeps = {}
    max_polls = 300  # 150 seconds max
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
            
            # Track sub-steps with their durations
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
                elif seen_substeps[sub_name]['status'] != sub_status:
                    old_status = seen_substeps[sub_name]['status']
                    seen_substeps[sub_name]['status'] = sub_status
                    if sub_duration:
                        seen_substeps[sub_name]['duration'] = sub_duration
        
        if status == 'completed':
            print("\n" + "=" * 80)
            print("✅ Processing completed!")
            print("=" * 80)
            break
        elif status == 'failed':
            print(f"\n❌ Processing failed: {job_status.get('error_message', 'Unknown error')}")
            break
        
        time.sleep(0.5)
        poll_count += 1
    
    # 4. Display detailed timing analysis
    print("\n" + "=" * 80)
    print("📝 Sub-steps Timing Analysis")
    print("=" * 80)
    
    SMALL_THRESHOLD = 0.01  # 10ms
    
    small_steps = []
    significant_steps = []
    
    for name, info in seen_substeps.items():
        duration = info.get('duration')
        if duration is not None:
            if duration < SMALL_THRESHOLD:
                small_steps.append((name, duration))
            else:
                significant_steps.append((name, duration))
    
    print(f"\n🔍 Steps with duration >= 10ms ({len(significant_steps)}):")
    for name, duration in sorted(significant_steps, key=lambda x: x[1], reverse=True):
        print(f"  • {name}: {duration*1000:.2f}ms")
    
    print(f"\n⚡ Steps with duration < 10ms ({len(small_steps)}):")
    total_small_duration = 0
    for name, duration in sorted(small_steps, key=lambda x: x[1], reverse=True):
        print(f"  • {name}: {duration*1000:.2f}ms")
        total_small_duration += duration
    
    print(f"\n📊 Summary:")
    print(f"  Total small steps: {len(small_steps)}")
    print(f"  Total small duration: {total_small_duration*1000:.2f}ms")
    print(f"  Total significant steps: {len(significant_steps)}")
    print(f"  Total steps: {len(seen_substeps)}")
    
    return True

if __name__ == "__main__":
    try:
        success = test_leclerc_substeps()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

