"""
Example test demonstrating LLM analysis functionality.
This is a manual test script to demonstrate the feature.
"""

import asyncio
import json
from app.services.llm_service_mock import LLMServiceMock


async def test_invoice_extraction():
    """Example: Extract invoice information from OCR content."""
    
    # Simulated OCR content (would come from Marker processing)
    ocr_content = """
    INVOICE
    
    ACME Corporation
    123 Business Street
    New York, NY 10001
    
    Invoice Number: INV-2024-0123
    Date: January 15, 2024
    
    Bill To:
    John Smith
    456 Customer Avenue
    Los Angeles, CA 90001
    
    Description                    Quantity    Price       Total
    Consulting Services            10 hours    $100.00     $1,000.00
    Software License               1           $250.00     $250.00
    
    Subtotal:                                              $1,250.00
    Tax (10%):                                             $125.00
    
    TOTAL DUE:                                             $1,375.00
    
    Payment Terms: Net 30 days
    """
    
    # Define extraction schema
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
            "description": "List of items or services on the invoice with descriptions",
            "required": False
        }
    }
    
    # Task introduction
    introduction = """
    Extract key invoice information from this document. 
    Focus on identifying the vendor, invoice number, dates, amounts, and line items.
    For amounts, extract numeric values only.
    """
    
    # Use mock service for testing
    llm_service = LLMServiceMock()
    
    print("=" * 80)
    print("LLM ANALYSIS EXAMPLE: Invoice Extraction")
    print("=" * 80)
    print("\nOCR Content (first 200 chars):")
    print(ocr_content[:200] + "...")
    print("\nSchema Fields:")
    for field_name, field_def in schema.items():
        req = "REQUIRED" if field_def.get("required") else "optional"
        print(f"  - {field_name} ({field_def['type']}, {req}): {field_def['description']}")
    
    print("\n" + "-" * 80)
    print("Running LLM Analysis...")
    print("-" * 80)
    
    # Perform analysis
    result = await llm_service.analyze_ocr_content(
        ocr_content=ocr_content,
        introduction=introduction,
        schema=schema
    )
    
    print("\nExtracted Data:")
    print(json.dumps(result, indent=2))
    print("\n" + "=" * 80)
    print("Analysis Complete!")
    print("=" * 80)


async def test_resume_extraction():
    """Example: Extract resume/CV information from OCR content."""
    
    ocr_content = """
    JOHN DOE
    Software Engineer
    
    Contact:
    Email: john.doe@email.com
    Phone: +1 (555) 123-4567
    LinkedIn: linkedin.com/in/johndoe
    
    PROFESSIONAL SUMMARY
    Experienced software engineer with 8 years of experience in full-stack development.
    Specialized in Python, JavaScript, and cloud technologies.
    
    SKILLS
    - Programming: Python, JavaScript, TypeScript, Java
    - Frameworks: React, FastAPI, Django, Node.js
    - Cloud: AWS, Docker, Kubernetes
    - Databases: PostgreSQL, MongoDB, Redis
    
    EXPERIENCE
    
    Senior Software Engineer | Tech Corp | 2020 - Present
    - Led development of microservices architecture
    - Improved system performance by 40%
    - Mentored junior developers
    
    Software Engineer | StartupXYZ | 2016 - 2020
    - Built RESTful APIs using Python and FastAPI
    - Implemented CI/CD pipelines
    - Developed frontend applications with React
    
    EDUCATION
    Bachelor of Science in Computer Science
    University of Technology | 2012 - 2016
    """
    
    schema = {
        "full_name": {
            "type": "string",
            "description": "Candidate's full name",
            "required": True
        },
        "email": {
            "type": "string",
            "description": "Email address",
            "required": False
        },
        "phone": {
            "type": "string",
            "description": "Phone number",
            "required": False
        },
        "current_title": {
            "type": "string",
            "description": "Current job title or most recent position",
            "required": False
        },
        "years_experience": {
            "type": "integer",
            "description": "Total years of professional experience",
            "required": False
        },
        "technical_skills": {
            "type": "array",
            "description": "List of technical skills, programming languages, and technologies",
            "required": False
        },
        "education": {
            "type": "string",
            "description": "Highest level of education and degree",
            "required": False
        }
    }
    
    introduction = """
    Extract key information from this resume/CV.
    Focus on contact details, professional experience, skills, and education.
    For years of experience, calculate from the work history provided.
    """
    
    llm_service = LLMServiceMock()
    
    print("\n\n" + "=" * 80)
    print("LLM ANALYSIS EXAMPLE: Resume/CV Extraction")
    print("=" * 80)
    
    result = await llm_service.analyze_ocr_content(
        ocr_content=ocr_content,
        introduction=introduction,
        schema=schema
    )
    
    print("\nExtracted Data:")
    print(json.dumps(result, indent=2))
    print("\n" + "=" * 80)


async def main():
    """Run all examples."""
    await test_invoice_extraction()
    await test_resume_extraction()


if __name__ == "__main__":
    print("\n🤖 LLM Analysis Examples")
    print("This script demonstrates the LLM analysis feature with mock data.\n")
    asyncio.run(main())

