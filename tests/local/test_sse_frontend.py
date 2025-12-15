#!/usr/bin/env python3
"""
Test script to simulate frontend SSE behavior and identify the issue.
This script uploads a file, starts processing, and immediately connects to SSE
to see if the connection is established correctly.
"""

import requests
import json
import time
import threading
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_sse_connection():
    print("=" * 80)
    print("Testing SSE connection behavior")
    print("=" * 80)
    
    # 1. Upload file
    print("\n1. Uploading file...")
    with open("tests/backend/FullStack/file-to-parse/exemple_facture.pdf", "rb") as f:
        upload_response = requests.post(
            f"{BASE_URL}/documents/upload",
            files={"file": f}
        )
    upload_response.raise_for_status()
    file_data = upload_response.json()
    file_id = file_data["file_id"]
    print(f"   ✅ File uploaded: {file_id}")
    
    # 2. Start processing
    print("\n2. Starting processing...")
    process_response = requests.post(
        f"{BASE_URL}/documents/process",
        data={
            "file_id": file_id,
            "output_format": "markdown",
            "paginate_output": "false"
        }
    )
    process_response.raise_for_status()
    job_data = process_response.json()
    job_id = job_data["job_id"]
    print(f"   ✅ Processing started: {job_id}")
    
    # 3. Immediately connect to SSE (simulating frontend behavior)
    print(f"\n3. Connecting to SSE stream immediately...")
    print(f"   URL: {BASE_URL}/documents/jobs/{job_id}/stream")
    
    sse_url = f"{BASE_URL}/documents/jobs/{job_id}/stream"
    start_time = time.time()
    
    try:
        response = requests.get(
            sse_url,
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=60
        )
        response.raise_for_status()
        
        print(f"   ✅ SSE connection established (took {time.time() - start_time:.2f}s)")
        print(f"   Status code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        # Read SSE events
        event_count = 0
        last_status = None
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    event_count += 1
                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    try:
                        data = json.loads(data_str)
                        current_status = data.get('status')
                        
                        if current_status != last_status:
                            print(f"\n   📨 Event #{event_count}: status={current_status}")
                            last_status = current_status
                            
                            if current_status == 'completed':
                                print(f"   ✅ Job completed!")
                                break
                            elif current_status == 'failed':
                                print(f"   ❌ Job failed!")
                                break
                    except json.JSONDecodeError as e:
                        print(f"   ⚠️  Failed to parse event: {e}")
                        print(f"   Raw data: {data_str[:100]}")
                elif line_str.startswith(': '):
                    # Keepalive comment
                    pass
                else:
                    print(f"   📝 Other line: {line_str[:100]}")
        
        print(f"\n   Total events received: {event_count}")
        print(f"   Connection duration: {time.time() - start_time:.2f}s")
        
    except requests.exceptions.Timeout:
        print(f"   ❌ SSE connection timeout after {time.time() - start_time:.2f}s")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ SSE connection error: {e}")
        print(f"   Error occurred after {time.time() - start_time:.2f}s")
    except KeyboardInterrupt:
        print(f"\n   ⚠️  Interrupted by user")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sse_connection()

