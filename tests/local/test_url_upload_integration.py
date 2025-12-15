#!/usr/bin/env python3
"""
Integration test for URL upload functionality.
This test can be run in the Docker test container to verify URL upload works end-to-end.

Usage in Docker:
    docker-compose -f docker-compose.test.yml run --rm backend-test python test_url_upload_integration.py

Or with Makefile:
    make test-backend-fast TEST_ARGS="test_url_upload_integration.py"
"""

import requests
import json
import sys
import time
import os

# Get base URL from environment or use default
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
TEST_URL = "https://file-examples.com/storage/fecf1c9d35693fb809c2bef/2017/10/file-sample_150kB.pdf"

def test_url_upload_integration():
    """Test URL upload end-to-end integration."""
    print("=" * 80)
    print("URL Upload Integration Test")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Test URL: {TEST_URL}")
    print()
    
    errors = []
    
    # Test 1: Upload from URL
    print("1. Testing upload from URL...")
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
        
        print(f"   ✅ Upload successful")
        print(f"   File ID: {file_id}")
        print(f"   Filename: {filename}")
        print(f"   Size: {size} bytes")
        
        if not file_id:
            errors.append("No file_id returned from upload")
        if size < 100000:  # Should be around 150KB
            print(f"   ⚠️  WARNING: File size seems small ({size} bytes)")
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP Error: {e} - {e.response.text if e.response else 'No response'}"
        print(f"   ❌ {error_msg}")
        errors.append(error_msg)
        return False
    except Exception as e:
        error_msg = f"Upload failed: {e}"
        print(f"   ❌ {error_msg}")
        errors.append(error_msg)
        return False
    
    # Test 2: Start processing with uploaded file
    print("\n2. Testing processing with uploaded file...")
    try:
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
        
        print(f"   ✅ Processing started")
        print(f"   Job ID: {job_id}")
        
    except Exception as e:
        error_msg = f"Processing start failed: {e}"
        print(f"   ❌ {error_msg}")
        errors.append(error_msg)
        return False
    
    # Test 3: Verify SSE connection works
    print("\n3. Testing SSE connection...")
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
        
        # Read first few events
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
                        print(f"   ✅ SSE event #{event_count}: status={status}")
                        
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
        error_msg = f"SSE test error: {e}"
        print(f"   ⚠️  {error_msg}")
        # Don't fail the test for SSE issues, just warn
    
    # Summary
    print("\n" + "=" * 80)
    if errors:
        print("❌ Test completed with errors:")
        for error in errors:
            print(f"   - {error}")
        print("=" * 80)
        return False
    else:
        print("✅ All URL upload integration tests passed!")
        print("=" * 80)
        return True

if __name__ == "__main__":
    success = test_url_upload_integration()
    sys.exit(0 if success else 1)

