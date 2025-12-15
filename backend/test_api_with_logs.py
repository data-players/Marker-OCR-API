#!/usr/bin/env python3
"""
Test script to process a document via API and check if step callbacks are working.
"""
import requests
import time
import sys

BASE_URL = "http://localhost:8000/api/v1/documents"

def test_upload_and_process():
    """Upload and process a document, checking step progression."""
    
    print("=" * 80)
    print("TEST: API document processing with step tracking")
    print("=" * 80)
    
    # 1. Upload a file
    print("\n1. Uploading exemple_facture.pdf...")
    with open("/app/uploads/exemple_facture.pdf", "rb") as f:
        files = {"file": ("exemple_facture.pdf", f, "application/pdf")}
        response = requests.post(f"{BASE_URL}/upload", files=files)
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return False
    
    upload_data = response.json()
    file_id = upload_data["file_id"]
    print(f"✅ File uploaded: {file_id}")
    
    # 2. Start processing
    print("\n2. Starting document processing...")
    process_data = {
        "file_id": file_id,
        "output_format": "markdown",
        "force_ocr": False,
        "extract_images": False
    }
    response = requests.post(f"{BASE_URL}/process", data=process_data)
    
    if response.status_code != 200:
        print(f"❌ Process failed: {response.status_code}")
        print(response.text)
        return False
    
    process_response = response.json()
    job_id = process_response["job_id"]
    print(f"✅ Processing started: {job_id}")
    
    # 3. Monitor job status
    print("\n3. Monitoring job status...")
    print("-" * 80)
    
    start_time = time.time()
    last_status = None
    step_updates = []
    
    while True:
        response = requests.get(f"{BASE_URL}/jobs/{job_id}")
        if response.status_code != 200:
            print(f"❌ Status check failed: {response.status_code}")
            break
        
        job_data = response.json()
        status = job_data["status"]
        steps = job_data.get("steps", [])
        
        if status != last_status:
            print(f"\n📊 Job Status: {status}")
            last_status = status
        
        # Show step details
        for step in steps:
            step_key = f"{step['name']}_{step['status']}"
            if step_key not in step_updates:
                step_updates.append(step_key)
                duration_str = f"{step.get('duration', 0):.3f}s" if step.get('duration') else "null"
                print(f"   [{step['status']:12}] {step['name']} - Duration: {duration_str}")
        
        if status in ["completed", "failed", "error"]:
            break
        
        if time.time() - start_time > 120:  # 2 minutes timeout
            print("\n⏱️ Timeout reached")
            break
        
        time.sleep(2)
    
    print("-" * 80)
    print("\n4. Final Summary:")
    print(f"   Total steps seen: {len(step_updates)}")
    print(f"   Final status: {status}")
    
    # Check durations
    steps_with_durations = [s for s in steps if s.get('duration') is not None and s.get('duration') > 0]
    steps_without_durations = [s for s in steps if not s.get('duration') or s.get('duration') <= 0]
    
    print(f"   Steps with valid durations: {len(steps_with_durations)}/{len(steps)}")
    print(f"   Steps without durations: {len(steps_without_durations)}/{len(steps)}")
    
    if steps_without_durations:
        print("\n   ⚠️ Steps missing durations:")
        for step in steps_without_durations:
            print(f"      - {step['name']} (status: {step['status']})")
    
    print("\n" + "=" * 80)
    
    if status == "completed" and len(steps_with_durations) > 0:
        print("✅ SUCCESS: Document processed with step tracking!")
        return True
    elif status == "completed" and len(steps_with_durations) == 0:
        print("❌ FAILURE: Document processed BUT no step durations recorded!")
        return False
    else:
        print(f"❌ FAILURE: Processing failed with status: {status}")
        return False

if __name__ == "__main__":
    success = test_upload_and_process()
    sys.exit(0 if success else 1)

