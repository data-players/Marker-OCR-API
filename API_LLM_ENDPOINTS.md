# API Documentation - LLM Analysis Endpoints

## Base URL

```
http://localhost:8000/api/v1
```

Production:
```
https://api.ocr.data-players.com/api/v1
```

---

## Endpoints

### 1. Start LLM Analysis

Start an LLM analysis on a completed OCR job.

**Endpoint:** `POST /llm/analyze`

**Request Body:**

```json
{
  "job_id": "string (uuid)",
  "introduction": "string",
  "schema": {
    "field_name": {
      "type": "string | number | integer | boolean | array | object | null",
      "description": "string",
      "required": "boolean (optional, default: false)"
    }
  }
}
```

**Example Request:**

```bash
curl -X POST http://localhost:8000/api/v1/llm/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "introduction": "Extract invoice information from this document",
    "schema": {
      "vendor_name": {
        "type": "string",
        "description": "Name of the vendor issuing the invoice",
        "required": true
      },
      "total_amount": {
        "type": "number",
        "description": "Total amount due including taxes",
        "required": true
      },
      "invoice_date": {
        "type": "string",
        "description": "Date of the invoice"
      }
    }
  }'
```

**Success Response (202 Accepted):**

```json
{
  "analysis_id": "660e8400-e29b-41d4-a716-446655440001",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "extracted_data": null,
  "error_message": null,
  "processing_time": 0.0,
  "created_at": "2025-12-16T10:30:00.000Z"
}
```

**Error Responses:**

**400 Bad Request** - Invalid request
```json
{
  "error": "Invalid job ID format",
  "status_code": 400
}
```

**404 Not Found** - Job not found
```json
{
  "error": "Job not found",
  "status_code": 404
}
```

**400 Bad Request** - Job not completed
```json
{
  "error": "OCR job must be completed before LLM analysis",
  "status_code": 400
}
```

---

### 2. Get Analysis Status

Get the status and results of an LLM analysis.

**Endpoint:** `GET /llm/analyze/{analysis_id}`

**Path Parameters:**
- `analysis_id` (string, uuid): Analysis identifier

**Example Request:**

```bash
curl http://localhost:8000/api/v1/llm/analyze/660e8400-e29b-41d4-a716-446655440001
```

**Success Response (200 OK) - Processing:**

```json
{
  "analysis_id": "660e8400-e29b-41d4-a716-446655440001",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": null,
  "extracted_data": null,
  "error_message": null
}
```

**Success Response (200 OK) - Completed:**

```json
{
  "analysis_id": "660e8400-e29b-41d4-a716-446655440001",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "extracted_data": {
    "vendor_name": "ACME Corporation",
    "total_amount": 1375.00,
    "invoice_date": "2024-01-15"
  },
  "error_message": null
}
```

**Success Response (200 OK) - Failed:**

```json
{
  "analysis_id": "660e8400-e29b-41d4-a716-446655440001",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "progress": null,
  "extracted_data": null,
  "error_message": "LLM returned invalid JSON"
}
```

**Error Response:**

**404 Not Found** - Analysis not found
```json
{
  "error": "Analysis not found",
  "status_code": 404
}
```

---

## Schema Field Types

### Supported Types

| Type | Description | Example Value |
|------|-------------|---------------|
| `string` | Text data | `"ACME Corp"` |
| `number` | Numeric value (float) | `1375.50` |
| `integer` | Integer value | `42` |
| `boolean` | True/false | `true` |
| `array` | List of items | `["item1", "item2"]` |
| `object` | Nested object | `{"key": "value"}` |
| `null` | Nullable field | `null` |

### Field Properties

- **type** (required): Data type of the field
- **description** (required): Explanation of what to extract
- **required** (optional): Whether field must be present (default: false)

---

## Complete Workflow Example

### Step 1: Upload Document

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@invoice.pdf"
```

Response:
```json
{
  "file_id": "450e8400-e29b-41d4-a716-446655440000",
  "filename": "invoice.pdf",
  "size": 102400
}
```

### Step 2: Process with OCR

```bash
curl -X POST http://localhost:8000/api/v1/documents/process \
  -F "file_id=450e8400-e29b-41d4-a716-446655440000" \
  -F "output_format=markdown"
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

### Step 3: Wait for OCR Completion

```bash
curl http://localhost:8000/api/v1/documents/jobs/550e8400-e29b-41d4-a716-446655440000
```

Wait until `status` is `"completed"`.

### Step 4: Start LLM Analysis

```bash
curl -X POST http://localhost:8000/api/v1/llm/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "introduction": "Extract invoice data",
    "schema": {
      "vendor": {"type": "string", "description": "Vendor name", "required": true},
      "total": {"type": "number", "description": "Total amount", "required": true}
    }
  }'
```

Response:
```json
{
  "analysis_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "processing"
}
```

### Step 5: Poll for Results

```bash
curl http://localhost:8000/api/v1/llm/analyze/660e8400-e29b-41d4-a716-446655440001
```

Poll every 1-2 seconds until `status` is `"completed"`.

Final response:
```json
{
  "analysis_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "completed",
  "extracted_data": {
    "vendor": "ACME Corporation",
    "total": 1375.00
  }
}
```

---

## Rate Limits

No rate limits currently enforced, but recommended:
- Max 10 concurrent analyses per user
- Max 100 analyses per hour

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |
| 503 | Service Unavailable - LLM API down |

---

## Best Practices

### 1. Schema Design

**Good:**
```json
{
  "invoice_date": {
    "type": "string",
    "description": "Invoice date in ISO format (YYYY-MM-DD) if possible",
    "required": true
  }
}
```

**Bad:**
```json
{
  "date": {
    "type": "string",
    "description": "date"
  }
}
```

### 2. Introduction Writing

**Good:**
```
Extract key invoice information including vendor name, invoice number, 
date, and total amount. For line items, extract description and price.
```

**Bad:**
```
Get data
```

### 3. Required Fields

Only mark fields as `required: true` if they are absolutely necessary.
Missing required fields will cause the analysis to fail.

### 4. Polling

Poll every 1-2 seconds. Don't poll more frequently to avoid unnecessary load.

---

## OpenAPI Specification

Full OpenAPI spec available at:
```
http://localhost:8000/docs
```

Interactive API documentation (Swagger UI):
```
http://localhost:8000/docs
```

Alternative documentation (ReDoc):
```
http://localhost:8000/redoc
```

---

## Authentication

The backend handles authentication with Infomaniak automatically using environment variables:
- `LLM_PRODUCT_ID`: Your Infomaniak AI product ID
- `LLM_API_TOKEN`: Your Bearer token

No additional authentication required from the frontend.

**API Endpoint Format**:
```
https://api.infomaniak.com/1/ai/{product_id}/openai/chat/completions
```

**Reference**: [Infomaniak AI API Documentation](https://developer.infomaniak.com/docs/api/post/1/ai/%7Bproduct_id%7D/openai/chat/completions)

---

## Support

For issues or questions:
- Check [LLM_ANALYSIS_GUIDE.md](LLM_ANALYSIS_GUIDE.md)
- View logs: `make dev-logs`
- Test with mock service first

---

**Version:** 1.1.0  
**Last Updated:** December 16, 2025

