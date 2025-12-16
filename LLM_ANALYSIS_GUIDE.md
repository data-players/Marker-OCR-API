# LLM Analysis Guide

## Overview

The LLM Analysis feature allows you to extract structured data from OCR results using an external Large Language Model (Infomaniak API). After processing a document with Marker OCR, you can define a JSON schema and let the LLM extract specific information according to your requirements.

## How It Works

1. **Process Document**: First, upload and process a document using the standard OCR workflow
2. **Define Schema**: Once OCR is complete, define a JSON schema with field types and descriptions
3. **Write Introduction**: Provide a task description explaining what information to extract
4. **Run Analysis**: The system calls the LLM with an optimized prompt containing:
   - Your introduction
   - The OCR content
   - The schema definition
5. **Get Results**: Receive structured JSON data matching your schema

## Configuration

### Backend Configuration

Add the following environment variables to your `.env` file:

```bash
# LLM Configuration (Infomaniak API)
LLM_PRODUCT_ID="105448"  # Your Infomaniak AI product ID
LLM_API_TOKEN="Bearer your_token_here"  # Your Bearer token
LLM_MODEL="gpt-3.5-turbo"  # or gpt-4, gpt-4-turbo for better accuracy
LLM_TIMEOUT=60  # API timeout in seconds
```

The API URL is automatically constructed as:
```
https://api.infomaniak.com/1/ai/{LLM_PRODUCT_ID}/openai/chat/completions
```

### Obtaining Infomaniak AI Credentials

1. Go to [Infomaniak AI Manager](https://manager.infomaniak.com/v3/ai)
2. Create or select your AI product
3. Note your **Product ID** (e.g., `105448`)
4. Generate an **API Bearer token**
5. Add both to your `.env` file

**Documentation**: [Infomaniak AI API](https://developer.infomaniak.com/docs/api/post/1/ai/%7Bproduct_id%7D/openai/chat/completions)

## API Usage

### Starting an LLM Analysis

**Endpoint:** `POST /api/v1/llm/analyze`

**Request Body:**
```json
{
  "job_id": "uuid-of-completed-ocr-job",
  "introduction": "Extract invoice information from this document. Focus on amounts, dates, and vendor details.",
  "schema": {
    "vendor_name": {
      "type": "string",
      "description": "Name of the vendor or company issuing the invoice",
      "required": true
    },
    "invoice_number": {
      "type": "string",
      "description": "Invoice number or reference",
      "required": true
    },
    "invoice_date": {
      "type": "string",
      "description": "Date of the invoice (ISO format if possible)",
      "required": false
    },
    "total_amount": {
      "type": "number",
      "description": "Total amount to pay including taxes",
      "required": true
    },
    "currency": {
      "type": "string",
      "description": "Currency code (e.g., USD, EUR)",
      "required": false
    },
    "line_items": {
      "type": "array",
      "description": "List of items or services on the invoice",
      "required": false
    }
  }
}
```

**Response:**
```json
{
  "analysis_id": "uuid-of-analysis",
  "job_id": "uuid-of-ocr-job",
  "status": "processing",
  "extracted_data": null,
  "error_message": null,
  "processing_time": 0.0
}
```

### Checking Analysis Status

**Endpoint:** `GET /api/v1/llm/analyze/{analysis_id}`

**Response (completed):**
```json
{
  "analysis_id": "uuid-of-analysis",
  "job_id": "uuid-of-ocr-job",
  "status": "completed",
  "progress": null,
  "extracted_data": {
    "vendor_name": "ACME Corporation",
    "invoice_number": "INV-2024-0123",
    "invoice_date": "2024-01-15",
    "total_amount": 1250.00,
    "currency": "USD",
    "line_items": [
      "Consulting services - $1000.00",
      "Software license - $250.00"
    ]
  },
  "error_message": null
}
```

## Schema Definition

### Supported Field Types

- `string`: Text data
- `number`: Numeric values (float)
- `integer`: Integer values
- `boolean`: True/false values
- `array`: List of items
- `object`: Nested object structure
- `null`: Nullable field

### Field Properties

- **type** (required): Data type of the field
- **description** (required): Explanation of what information to extract
- **required** (optional, default: false): Whether the field must be present

### Example Schemas

#### Invoice Extraction

```json
{
  "vendor_name": {
    "type": "string",
    "description": "Company name issuing the invoice",
    "required": true
  },
  "total_amount": {
    "type": "number",
    "description": "Total amount including taxes",
    "required": true
  },
  "items": {
    "type": "array",
    "description": "List of purchased items or services"
  }
}
```

#### Resume/CV Extraction

```json
{
  "full_name": {
    "type": "string",
    "description": "Candidate's full name",
    "required": true
  },
  "email": {
    "type": "string",
    "description": "Email address"
  },
  "phone": {
    "type": "string",
    "description": "Phone number"
  },
  "skills": {
    "type": "array",
    "description": "List of technical skills and competencies"
  },
  "years_experience": {
    "type": "integer",
    "description": "Total years of professional experience"
  }
}
```

#### Contract Extraction

```json
{
  "parties": {
    "type": "array",
    "description": "Names of all parties involved in the contract"
  },
  "effective_date": {
    "type": "string",
    "description": "Date when the contract becomes effective"
  },
  "termination_date": {
    "type": "string",
    "description": "Date when the contract terminates or expires"
  },
  "payment_terms": {
    "type": "string",
    "description": "Payment terms and conditions"
  },
  "auto_renewal": {
    "type": "boolean",
    "description": "Whether the contract automatically renews"
  }
}
```

## Frontend Usage

The frontend provides an intuitive interface for LLM analysis:

1. **After OCR completion**, a new section appears: "AI-Powered Data Extraction"
2. **Click "Start Analysis"** to show the analysis form
3. **Write Introduction**: Describe the extraction task
4. **Define Schema**: 
   - Add fields with the "Add Field" button
   - Set field name, type, description, and required status
   - Remove unwanted fields with the trash icon
5. **Start Analysis**: Click "Start LLM Analysis"
6. **View Results**: Structured JSON data appears when complete

### Component Integration

```tsx
import LLMAnalysis from '@/components/LLMAnalysis'

// In your component
<LLMAnalysis
  jobId={currentJobId}
  onAnalysisComplete={(data) => {
    console.log('Extracted data:', data)
    // Handle the extracted data
  }}
/>
```

## Architecture

### Backend Services

- **`llm_service.py`**: Real LLM service making API calls to Infomaniak
- **`llm_service_mock.py`**: Mock service for testing without API costs
- **`llm_models.py`**: Pydantic models for request/response validation
- **`llm_analysis.py`**: API endpoints for LLM analysis

### Frontend Components

- **`LLMAnalysis.tsx`**: Main component for schema editing and analysis
- **`api.ts`**: API client methods for LLM endpoints

### Data Flow

1. User defines schema and introduction in frontend
2. Frontend sends request to `/api/v1/llm/analyze`
3. Backend validates request and retrieves OCR content from Redis
4. Backend builds optimized prompt with OCR + schema + introduction
5. Backend calls Infomaniak API with prompt
6. LLM returns structured JSON
7. Backend validates result against schema
8. Backend stores result in Redis
9. Frontend polls for status and displays result

## Testing

### Unit Tests (modelFree)

The mock service is automatically used in test environments:

```python
# In tests/backend/modelFree/conftest.py
from app.services.llm_service_mock import LLMServiceMock

@pytest.fixture
def llm_service():
    return LLMServiceMock()
```

### Manual Testing

```bash
# 1. Process a document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@invoice.pdf"
  
curl -X POST http://localhost:8000/api/v1/documents/process \
  -F "file_id=your-file-id" \
  -F "output_format=markdown"

# 2. Wait for completion, then analyze
curl -X POST http://localhost:8000/api/v1/llm/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "your-job-id",
    "introduction": "Extract invoice data",
    "schema": {
      "vendor": {"type": "string", "description": "Vendor name", "required": true},
      "total": {"type": "number", "description": "Total amount", "required": true}
    }
  }'

# 3. Check status
curl http://localhost:8000/api/v1/llm/analyze/{analysis_id}
```

## Best Practices

### Writing Good Introductions

✅ **Good:**
```
Extract key invoice information from this document. Focus on identifying the vendor name, invoice number, date, and total amount. For line items, extract the description and price of each item.
```

❌ **Bad:**
```
Get the data
```

### Writing Good Schema Descriptions

✅ **Good:**
```json
{
  "invoice_date": {
    "type": "string",
    "description": "The date the invoice was issued, in ISO format (YYYY-MM-DD) if possible"
  }
}
```

❌ **Bad:**
```json
{
  "invoice_date": {
    "type": "string",
    "description": "date"
  }
}
```

### Optimizing for Accuracy

1. **Be Specific**: Clear descriptions help the LLM understand what to extract
2. **Use Examples**: Include format examples in descriptions
3. **Mark Required Fields**: Use `required: true` for critical data
4. **Choose Right Model**: GPT-4 is more accurate but slower/costlier than GPT-3.5
5. **Validate Results**: Always check extracted data for accuracy

### Performance Considerations

- **API Calls**: Each analysis makes one API call to Infomaniak
- **Cost**: Depends on document length and model (GPT-3.5 vs GPT-4)
- **Timeout**: Default 60s, increase for large documents
- **Retry Logic**: Automatic retry up to 3 times on failure

## Troubleshooting

### "LLM API key not configured"

Add `LLM_API_KEY` to your `.env` file and restart the backend.

### "Failed to parse JSON from LLM response"

The LLM returned invalid JSON. This can happen with:
- Very complex schemas
- Very long documents
- Lower-quality models

**Solutions:**
- Simplify the schema
- Use a better model (GPT-4)
- Increase timeout
- Improve introduction clarity

### "Required field missing from LLM response"

The LLM couldn't find the required field in the document.

**Solutions:**
- Check if the field actually exists in the document
- Improve field description
- Make field optional instead of required
- Check OCR quality

### "Analysis timeout"

The LLM took too long to respond.

**Solutions:**
- Increase `LLM_TIMEOUT` in settings
- Use a faster model
- Reduce document complexity
- Split large documents

## Future Enhancements

Potential improvements for future versions:

- **Streaming Results**: Real-time partial results as LLM processes
- **Batch Analysis**: Analyze multiple documents with same schema
- **Schema Templates**: Pre-defined schemas for common document types
- **Validation Rules**: Custom validation for extracted data
- **Multi-language Support**: Better handling of non-English documents
- **Cost Tracking**: Monitor API usage and costs
- **Result History**: Store and compare previous analyses

## Support

For issues or questions about LLM analysis:

1. Check configuration in `.env`
2. Verify Infomaniak API key is valid
3. Check backend logs for detailed errors
4. Test with mock service first (set `ENVIRONMENT=test`)

## References

- [Infomaniak API Documentation](https://developer.infomaniak.com/)
- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat)
- [Pydantic Models Documentation](https://docs.pydantic.dev/)

