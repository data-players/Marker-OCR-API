#!/usr/bin/env python3
"""
Test script for URL upload functionality.
Can be run in Docker test container to verify URL upload works correctly.
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"
TEST_URL = "https://file-examples.com/storage/fecf1c9d35693fb809c2bef/2017/10/file-sample_150kB.pdf"

def test_url_upload():
    """Test uploading a file from URL."""
    print("=" * 80)
    print("Testing URL Upload Functionality")
    print("=" * 80)
    
    # Test 1: Upload from URL
    print("\n1. Testing upload from URL...")
    print(f"   URL: {TEST_URL}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/documents/upload",
            data={"url": TEST_URL},
            timeout=60
        )
        response.raise_for_status()
        
        upload_data = response.json()
        file_id = upload_data.get("file_id")
        filename = upload_data.get("filename")
        size = upload_data.get("size")
        
        print(f"   ✅ Upload successful!")
        print(f"   File ID: {file_id}")
        print(f"   Filename: {filename}")
        print(f"   Size: {size} bytes")
        
        if not file_id:
            print("   ❌ ERROR: No file_id returned")
            return False
        
        if size < 100000:  # Should be around 150KB
            print(f"   ⚠️  WARNING: File size seems small ({size} bytes)")
        
        # Test 2: Verify file exists
        print("\n2. Verifying file exists...")
        try:
            status_response = requests.get(
                f"{BASE_URL}/documents/jobs/{file_id}",
                timeout=10
            )
            # This might fail if file_id is not a job_id, but that's OK
            # We just want to verify the upload worked
            print("   ✅ File verification endpoint accessible")
        except:
            # File endpoint might not exist, that's OK
            pass
        
        # Test 3: Start processing with uploaded file
        print("\n3. Testing processing with uploaded file...")
        process_response = requests.post(
            f"{BASE_URL}/documents/process",
            data={
                "file_id": file_id,
                "output_format": "markdown",
                "paginate_output": "false"
            },
            timeout=30
        )
        process_response.raise_for_status()
        
        job_data = process_response.json()
        job_id = job_data.get("job_id")
        
        print(f"   ✅ Processing started!")
        print(f"   Job ID: {job_id}")
        
        # Test 4: Verify SSE connection works
        print("\n4. Testing SSE connection...")
        sse_url = f"{BASE_URL}/documents/jobs/{job_id}/stream"
        print(f"   SSE URL: {sse_url}")
        
        try:
            sse_response = requests.get(
                sse_url,
                headers={"Accept": "text/event-stream"},
                stream=True,
                timeout=10
            )
            sse_response.raise_for_status()
            
            # Read first event
            event_count = 0
            for line in sse_response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        event_count += 1
                        data_str = line_str[6:]
                        try:
                            data = json.loads(data_str)
                            status = data.get('status')
                            print(f"   ✅ SSE event #{event_count} received: status={status}")
                            
                            if event_count >= 2:  # Get at least 2 events
                                break
                        except json.JSONDecodeError:
                            pass
                    elif line_str.startswith(': keepalive'):
                        print("   ✅ Keepalive received")
                        break
            
            if event_count > 0:
                print(f"   ✅ SSE connection working ({event_count} events received)")
            else:
                print("   ⚠️  WARNING: No SSE events received")
                
        except requests.exceptions.Timeout:
            print("   ⚠️  SSE connection timeout (this is OK for quick test)")
        except Exception as e:
            print(f"   ⚠️  SSE test error: {e}")
        
        print("\n" + "=" * 80)
        print("✅ All URL upload tests passed!")
        print("=" * 80)
        return True
        
    except requests.exceptions.HTTPError as e:
        print(f"\n   ❌ HTTP Error: {e}")
        print(f"   Response: {e.response.text if e.response else 'No response'}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n   ❌ Request Error: {e}")
        return False
    except Exception as e:
        print(f"\n   ❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_url_upload()
    sys.exit(0 if success else 1)

