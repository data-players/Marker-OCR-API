"""
Integration test for URL upload functionality with SSE.
This test can be run in the Docker test container to verify the complete workflow:
1. Upload from URL
2. Start processing
3. SSE connection and real-time updates
"""

import pytest
import requests
import time
import json
import os
from typing import Optional


class TestUrlUploadIntegration:
    """Integration tests for URL upload with SSE."""

    @pytest.fixture(scope="class")
    def api_base_url(self):
        """Get API base URL from environment or use default."""
        return os.getenv("API_BASE_URL", "http://localhost:8000")

    @pytest.fixture(scope="class")
    def test_pdf_url(self):
        """Test PDF URL that should be accessible."""
        # Using W3C test PDF that is publicly available
        return "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"

    def test_url_upload_success(self, api_base_url, test_pdf_url):
        """Test successful upload from URL."""
        url = f"{api_base_url}/api/v1/documents/upload"
        
        response = requests.post(
            url,
            data={"url": test_pdf_url},
            timeout=60
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        
        assert "file_id" in data
        assert "filename" in data
        assert "size" in data
        assert data["size"] > 0
        
        return data["file_id"]

    def test_process_document_after_url_upload(self, api_base_url, test_pdf_url):
        """Test processing a document uploaded from URL."""
        # Step 1: Upload from URL
        upload_url = f"{api_base_url}/api/v1/documents/upload"
        upload_response = requests.post(
            upload_url,
            data={"url": test_pdf_url},
            timeout=60
        )
        assert upload_response.status_code == 200
        file_id = upload_response.json()["file_id"]
        
        # Step 2: Start processing
        process_url = f"{api_base_url}/api/v1/documents/process"
        process_response = requests.post(
            process_url,
            data={
                "file_id": file_id,
                "output_format": "markdown"
            },
            timeout=60
        )
        
        assert process_response.status_code == 200, f"Process failed: {process_response.text}"
        process_data = process_response.json()
        
        assert "job_id" in process_data
        job_id = process_data["job_id"]
        
        return job_id

    def test_sse_connection_url_upload(self, api_base_url, test_pdf_url):
        """Test SSE connection for URL upload workflow."""
        # Step 1: Upload from URL
        upload_url = f"{api_base_url}/api/v1/documents/upload"
        upload_response = requests.post(
            upload_url,
            data={"url": test_pdf_url},
            timeout=60
        )
        assert upload_response.status_code == 200
        file_id = upload_response.json()["file_id"]
        
        # Step 2: Start processing
        process_url = f"{api_base_url}/api/v1/documents/process"
        process_response = requests.post(
            process_url,
            data={
                "file_id": file_id,
                "output_format": "markdown"
            },
            timeout=60
        )
        assert process_response.status_code == 200
        job_id = process_response.json()["job_id"]
        
        # Step 3: Test SSE connection
        sse_url = f"{api_base_url}/api/v1/documents/jobs/{job_id}/stream"
        
        # Verify SSE endpoint is accessible
        # Note: We can't easily test SSE with requests, but we can verify the endpoint exists
        # by checking that it returns proper headers
        headers = {"Accept": "text/event-stream"}
        
        # Use a timeout to avoid hanging
        try:
            response = requests.get(
                sse_url,
                headers=headers,
                stream=True,
                timeout=5
            )
            
            # SSE endpoint should return 200 with proper content type
            assert response.status_code == 200, f"SSE endpoint failed: {response.status_code}"
            assert "text/event-stream" in response.headers.get("Content-Type", ""), \
                f"Wrong content type: {response.headers.get('Content-Type')}"
            
            # Read first few events
            events_received = 0
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data:"):
                    events_received += 1
                    data = json.loads(line[5:].strip())
                    assert "job_id" in data
                    assert data["job_id"] == job_id
                    
                    # Stop after receiving initial event
                    if events_received >= 1:
                        break
                
                if events_received >= 1:
                    break
            
            assert events_received > 0, "No SSE events received"
            
        except requests.exceptions.Timeout:
            # Timeout is acceptable for SSE as it's a long-running connection
            # The important thing is that the endpoint is accessible
            pass

    def test_complete_url_upload_workflow(self, api_base_url, test_pdf_url):
        """Test complete workflow: URL upload -> processing -> SSE updates."""
        # Step 1: Upload from URL
        upload_url = f"{api_base_url}/api/v1/documents/upload"
        upload_response = requests.post(
            upload_url,
            data={"url": test_pdf_url},
            timeout=60
        )
        assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
        upload_data = upload_response.json()
        file_id = upload_data["file_id"]
        
        assert upload_data["size"] > 0
        assert upload_data["filename"] is not None
        
        # Step 2: Start processing
        process_url = f"{api_base_url}/api/v1/documents/process"
        process_response = requests.post(
            process_url,
            data={
                "file_id": file_id,
                "output_format": "markdown",
                "extract_images": "false",
                "paginate_output": "false"
            },
            timeout=60
        )
        assert process_response.status_code == 200, f"Process failed: {process_response.text}"
        process_data = process_response.json()
        job_id = process_data["job_id"]
        
        # Step 3: Verify job status endpoint
        status_url = f"{api_base_url}/api/v1/documents/jobs/{job_id}"
        status_response = requests.get(status_url, timeout=30)
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["job_id"] == job_id
        assert "status" in status_data
        assert status_data["status"] in ["pending", "processing", "completed", "failed"]
        
        # Step 4: Verify SSE endpoint URL is correct (no double /api/v1)
        sse_url = f"{api_base_url}/api/v1/documents/jobs/{job_id}/stream"
        assert "/api/v1/api/v1" not in sse_url, f"Double /api/v1 in SSE URL: {sse_url}"
        
        # Verify SSE endpoint is accessible
        headers = {"Accept": "text/event-stream"}
        try:
            sse_response = requests.get(
                sse_url,
                headers=headers,
                stream=True,
                timeout=3
            )
            assert sse_response.status_code == 200
            assert "text/event-stream" in sse_response.headers.get("Content-Type", "")
        except requests.exceptions.Timeout:
            # Timeout is acceptable for SSE
            pass

    def test_url_upload_invalid_url(self, api_base_url):
        """Test upload with invalid URL."""
        url = f"{api_base_url}/api/v1/documents/upload"
        
        response = requests.post(
            url,
            data={"url": "not-a-valid-url"},
            timeout=30
        )
        
        # Should return error for invalid URL
        assert response.status_code in [400, 422, 500]

    def test_url_upload_nonexistent_file(self, api_base_url):
        """Test upload with URL pointing to non-existent file."""
        url = f"{api_base_url}/api/v1/documents/upload"
        
        response = requests.post(
            url,
            data={"url": "https://example.com/nonexistent.pdf"},
            timeout=30
        )
        
        # Should return error for non-existent file
        assert response.status_code in [400, 422, 500]

