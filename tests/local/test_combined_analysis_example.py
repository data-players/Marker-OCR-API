"""
Example test demonstrating combined OCR + LLM analysis functionality.
This is a manual test script to demonstrate the one-shot API feature.
"""

import asyncio
import json
import httpx
import time


async def test_combined_invoice_analysis():
    """
    Example: Combined OCR + LLM analysis for invoice extraction.
    This demonstrates the one-shot API that processes a document from URL
    and extracts structured data in a single request.
    """
    
    # Base API URL (adjust based on your environment)
    base_url = "http://localhost:8000/api/v1"
    
    # Example document URL (replace with actual PDF URL)
    document_url = "https://example.com/sample-invoice.pdf"
    
    # Define extraction schema for invoice
    schema = {
        "vendor_name": {
            "type": "string",
            "description": "Name of the company issuing the invoice",
            "required": True
        },
        "invoice_number": {
            "type": "string",
            "description": "Invoice number or reference ID",
            "required": True
        },
        "invoice_date": {
            "type": "string",
            "description": "Date the invoice was issued",
            "required": True
        },
        "customer_name": {
            "type": "string",
            "description": "Name of the customer being billed",
            "required": False
        },
        "subtotal": {
            "type": "number",
            "description": "Subtotal amount before tax",
            "required": False
        },
        "tax_amount": {
            "type": "number",
            "description": "Tax amount",
            "required": False
        },
        "total_amount": {
            "type": "number",
            "description": "Total amount due including tax",
            "required": True
        },
        "currency": {
            "type": "string",
            "description": "Currency code (e.g., USD, EUR)",
            "required": False
        },
        "payment_terms": {
            "type": "string",
            "description": "Payment terms and conditions",
            "required": False
        },
        "line_items": {
            "type": "array",
            "description": "List of items or services on the invoice",
            "required": False
        }
    }
    
    # Task introduction for LLM
    introduction = """
    Extract key invoice information from this document. 
    Focus on identifying the vendor, invoice number, dates, amounts, and line items.
    For amounts, extract numeric values only (without currency symbols).
    Ensure all required fields are present.
    """
    
    # OCR options (optional, uses defaults if not provided)
    ocr_options = {
        "output_format": "markdown",
        "force_ocr": False,
        "extract_images": False,
        "paginate_output": False,
        "language": None
    }
    
    print("=" * 80)
    print("COMBINED ANALYSIS EXAMPLE: Invoice Extraction from URL")
    print("=" * 80)
    print(f"\nDocument URL: {document_url}")
    print("\nExtraction Schema:")
    for field_name, field_def in schema.items():
        req = "REQUIRED" if field_def.get("required") else "optional"
        print(f"  - {field_name} ({field_def['type']}, {req}): {field_def['description']}")
    
    print("\n" + "-" * 80)
    print("Step 1: Submitting combined analysis request...")
    print("-" * 80)
    
    # Submit combined analysis request
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            # POST request to combined analysis endpoint
            response = await client.post(
                f"{base_url}/combined/analyze-url",
                json={
                    "url": document_url,
                    "introduction": introduction,
                    "schema": schema,
                    "ocr_options": ocr_options
                }
            )
            response.raise_for_status()
            
            result = response.json()
            combined_job_id = result.get("combined_job_id")
            
            print(f"\n✅ Request submitted successfully!")
            print(f"Combined Job ID: {combined_job_id}")
            print(f"Status: {result.get('status')}")
            print(f"Phases: {', '.join(result.get('phases', []))}")
            
            print("\n" + "-" * 80)
            print("Step 2: Polling for job completion...")
            print("-" * 80)
            
            # Poll for job completion
            max_attempts = 60  # 5 minutes max
            poll_interval = 5  # 5 seconds
            
            for attempt in range(max_attempts):
                await asyncio.sleep(poll_interval)
                
                # Get job status
                status_response = await client.get(
                    f"{base_url}/combined/jobs/{combined_job_id}"
                )
                status_response.raise_for_status()
                
                status_data = status_response.json()
                current_status = status_data.get("status")
                current_phase = status_data.get("current_phase")
                
                print(f"[Attempt {attempt + 1}] Status: {current_status} | Phase: {current_phase}")
                
                if current_status == "completed":
                    print("\n" + "=" * 80)
                    print("✅ COMBINED ANALYSIS COMPLETED!")
                    print("=" * 80)
                    
                    # Display final results
                    final_result = status_data.get("final_result", {})
                    extracted_data = final_result.get("extracted_data", {})
                    
                    print("\nExtracted Data:")
                    print(json.dumps(extracted_data, indent=2))
                    
                    print("\nProcessing Times:")
                    print(f"  - Total: {final_result.get('total_processing_time', 0):.2f}s")
                    print(f"  - OCR: {final_result.get('ocr_processing_time', 0):.2f}s")
                    print(f"  - LLM: {final_result.get('llm_processing_time', 0):.2f}s")
                    
                    print("\n" + "=" * 80)
                    break
                    
                elif current_status == "failed":
                    print("\n❌ Analysis failed!")
                    print(f"Error: {status_data.get('error_message')}")
                    break
            else:
                print("\n⏱️ Timeout: Job did not complete within expected time")
                
        except httpx.HTTPError as e:
            print(f"\n❌ HTTP Error: {str(e)}")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


async def test_combined_receipt_analysis():
    """
    Example: Combined analysis for receipt extraction.
    Simpler schema focused on basic receipt information.
    """
    
    base_url = "http://localhost:8000/api/v1"
    document_url = "https://example.com/receipt.pdf"
    
    # Simpler schema for receipts
    schema = {
        "merchant_name": {
            "type": "string",
            "description": "Name of the merchant or store",
            "required": True
        },
        "date": {
            "type": "string",
            "description": "Transaction date",
            "required": True
        },
        "total_amount": {
            "type": "number",
            "description": "Total amount paid",
            "required": True
        },
        "payment_method": {
            "type": "string",
            "description": "Payment method used (cash, credit card, etc.)",
            "required": False
        },
        "items": {
            "type": "array",
            "description": "List of purchased items",
            "required": False
        }
    }
    
    introduction = """
    Extract receipt information including merchant name, date, total amount, 
    and list of items purchased.
    """
    
    print("\n\n" + "=" * 80)
    print("COMBINED ANALYSIS EXAMPLE: Receipt Extraction")
    print("=" * 80)
    print(f"\nDocument URL: {document_url}")
    print("\nThis example demonstrates a simpler extraction schema for receipts.")
    print("\nSchema Fields:")
    for field_name, field_def in schema.items():
        req = "REQUIRED" if field_def.get("required") else "optional"
        print(f"  - {field_name} ({field_def['type']}, {req})")
    print("\n" + "=" * 80)


async def main():
    """Run all examples."""
    print("\n🤖 Combined Analysis API Examples")
    print("This script demonstrates the one-shot OCR + LLM analysis feature.\n")
    print("⚠️  NOTE: Update the document URLs in the code with actual PDF URLs.\n")
    
    # Run invoice example
    await test_combined_invoice_analysis()
    
    # Show receipt example (schema only)
    await test_combined_receipt_analysis()


if __name__ == "__main__":
    asyncio.run(main())

