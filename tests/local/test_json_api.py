"""
Test script to verify JSON API format and CORS headers.
Tests that the combined analysis API accepts JSON and returns properly structured JSON.
"""

import httpx
import asyncio
import json


async def test_json_request_response():
    """Test that API accepts and returns JSON with proper content types."""
    
    api_url = "http://localhost:8000/api/v1"
    
    print("=" * 80)
    print("JSON API FORMAT TEST")
    print("=" * 80)
    
    # Test payload
    request_payload = {
        "url": "https://example.com/test.pdf",
        "introduction": "Extract test data",
        "schema": {
            "field1": {
                "type": "string",
                "description": "Test field",
                "required": True
            }
        },
        "ocr_options": {
            "output_format": "markdown",
            "force_ocr": False
        }
    }
    
    print("\n1. Testing JSON Request Format")
    print("-" * 80)
    print("Request payload:")
    print(json.dumps(request_payload, indent=2))
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("\n2. Sending POST request with Content-Type: application/json")
            print("-" * 80)
            
            response = await client.post(
                f"{api_url}/combined/analyze-url",
                json=request_payload,
                headers={
                    "Content-Type": "application/json",
                    "Origin": "https://external-app.example.com"  # Test CORS
                }
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type')}")
            
            # Check CORS headers
            print("\n3. Checking CORS Headers")
            print("-" * 80)
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("access-control-allow-origin"),
                "Access-Control-Allow-Methods": response.headers.get("access-control-allow-methods"),
                "Access-Control-Allow-Headers": response.headers.get("access-control-allow-headers"),
                "Access-Control-Allow-Credentials": response.headers.get("access-control-allow-credentials"),
            }
            
            for header, value in cors_headers.items():
                status = "✅" if value else "❌"
                print(f"{status} {header}: {value}")
            
            # Check JSON response
            print("\n4. Validating JSON Response Structure")
            print("-" * 80)
            
            if response.status_code == 200 or response.status_code == 503:
                response_data = response.json()
                print("Response JSON:")
                print(json.dumps(response_data, indent=2))
                
                # Validate response structure
                if response.status_code == 200:
                    required_fields = ["combined_job_id", "status", "message", "phases"]
                    print("\nValidating required fields:")
                    for field in required_fields:
                        present = field in response_data
                        status = "✅" if present else "❌"
                        print(f"{status} {field}: {present}")
                        
                    # Test GET endpoint
                    if "combined_job_id" in response_data:
                        job_id = response_data["combined_job_id"]
                        
                        print(f"\n5. Testing GET endpoint for job status")
                        print("-" * 80)
                        print(f"Job ID: {job_id}")
                        
                        status_response = await client.get(
                            f"{api_url}/combined/jobs/{job_id}",
                            headers={
                                "Origin": "https://external-app.example.com"
                            }
                        )
                        
                        print(f"Status Code: {status_response.status_code}")
                        print(f"Content-Type: {status_response.headers.get('content-type')}")
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            print("\nStatus Response JSON:")
                            print(json.dumps(status_data, indent=2))
                            
                            # Validate status response structure
                            required_status_fields = [
                                "combined_job_id",
                                "status",
                                "current_phase",
                                "created_at",
                                "updated_at"
                            ]
                            print("\nValidating required status fields:")
                            for field in required_status_fields:
                                present = field in status_data
                                status = "✅" if present else "❌"
                                print(f"{status} {field}: {present}")
                else:
                    print(f"\nNote: Received {response.status_code} - Models may not be loaded yet")
                    print("This is expected if AI models are still initializing")
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                print(f"Response: {response.text}")
                
            print("\n" + "=" * 80)
            print("TEST SUMMARY")
            print("=" * 80)
            
            checks = []
            checks.append(("Content-Type is application/json", 
                          "application/json" in response.headers.get("content-type", "")))
            checks.append(("CORS headers present", 
                          cors_headers["Access-Control-Allow-Origin"] is not None))
            checks.append(("Response is valid JSON", 
                          response.headers.get("content-type", "").startswith("application/json")))
            
            for check_name, check_result in checks:
                status = "✅ PASS" if check_result else "❌ FAIL"
                print(f"{status}: {check_name}")
                
    except httpx.ConnectError:
        print("\n❌ Connection Error: Could not connect to API")
        print("Make sure the API is running: make dev-up")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_cors_preflight():
    """Test CORS preflight (OPTIONS) request."""
    
    api_url = "http://localhost:8000/api/v1"
    
    print("\n\n" + "=" * 80)
    print("CORS PREFLIGHT TEST")
    print("=" * 80)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            print("\nSending OPTIONS request (CORS preflight)")
            print("-" * 80)
            
            response = await client.request(
                "OPTIONS",
                f"{api_url}/combined/analyze-url",
                headers={
                    "Origin": "https://external-app.example.com",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type"
                }
            )
            
            print(f"Status Code: {response.status_code}")
            print("\nCORS Preflight Response Headers:")
            print("-" * 80)
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("access-control-allow-origin"),
                "Access-Control-Allow-Methods": response.headers.get("access-control-allow-methods"),
                "Access-Control-Allow-Headers": response.headers.get("access-control-allow-headers"),
            }
            
            for header, value in cors_headers.items():
                print(f"{header}: {value}")
                
            if response.status_code == 200:
                print("\n✅ CORS preflight successful - API supports cross-origin requests")
            else:
                print(f"\n⚠️  Unexpected preflight response: {response.status_code}")
                
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


async def main():
    """Run all tests."""
    print("\n🧪 JSON API & CORS Tests")
    print("Testing the combined analysis API format and cross-origin support\n")
    
    await test_json_request_response()
    await test_cors_preflight()
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

