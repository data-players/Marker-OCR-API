# Changelog - LLM Analysis Feature

## Version 1.1.0 - LLM Analysis Feature

**Date**: December 16, 2025

### 🎉 New Feature: AI-Powered Data Extraction

Added comprehensive LLM analysis functionality to extract structured data from OCR results using external LLM API (Infomaniak).

---

## Backend Changes

### New Services

#### `backend/app/services/llm_service.py`
- **LLMService**: Production service for calling Infomaniak LLM API
- Optimized prompt generation for data extraction
- Automatic retry logic (3 attempts)
- JSON validation against schema
- Support for OpenAI-compatible API format

#### `backend/app/services/llm_service_mock.py`
- **LLMServiceMock**: Test service without external API calls
- Generates mock data matching schema
- Fast execution for unit tests (<1s)

### New Models

#### `backend/app/models/llm_models.py`
- **SchemaFieldDefinition**: Schema field with type, description, required flag
- **LLMAnalysisRequest**: Request model with job_id, introduction, schema
- **LLMAnalysisResponse**: Response with analysis_id, status, extracted_data
- **LLMAnalysisStatus**: Status model for polling analysis progress

### New API Endpoints

#### `backend/app/api/routes/llm_analysis.py`
- `POST /api/v1/llm/analyze`: Start LLM analysis
- `GET /api/v1/llm/analyze/{analysis_id}`: Get analysis status

### Configuration

#### `backend/app/core/config.py`
Added LLM configuration settings:
- `llm_api_url`: LLM API endpoint (default: Infomaniak)
- `llm_api_key`: API authentication key
- `llm_model`: Model to use (default: gpt-3.5-turbo)
- `llm_timeout`: API timeout in seconds (default: 60)

### Dependencies

#### `backend/app/api/dependencies.py`
- Added `get_llm_service()` dependency injection
- Added LLM service cleanup on shutdown

#### `backend/app/services/redis_service.py`
Added analysis storage methods:
- `store_analysis()`: Store analysis data
- `get_analysis()`: Retrieve analysis data
- `update_analysis()`: Update analysis status
- `delete_analysis()`: Delete analysis data

### Main Application

#### `backend/app/main.py`
- Registered LLM analysis router
- Added `/api/v1/llm/*` endpoints to API

---

## Frontend Changes

### New Components

#### `frontend/src/components/LLMAnalysis.tsx`
Full-featured LLM analysis component with:
- **Introduction Editor**: Textarea for task description
- **Schema Builder**: 
  - Add/remove fields dynamically
  - Field name, type, description, required flag
  - Support for 6 data types (string, number, integer, boolean, array, object)
- **Validation**: Client-side validation before submission
- **Status Polling**: Automatic polling for analysis completion
- **Result Display**: Pretty-printed JSON result
- **Error Handling**: User-friendly error messages

### API Service Updates

#### `frontend/src/services/api.ts`
Added LLM analysis API methods:
- `analyzeLLM()`: Submit analysis request
- `getLLMAnalysisStatus()`: Poll analysis status

Added TypeScript interfaces:
- `SchemaFieldDefinition`
- `LLMAnalysisRequest`
- `LLMAnalysisResponse`
- `LLMAnalysisStatus`

### Page Integration

#### `frontend/src/pages/ProcessDocument.tsx`
- Added LLM analysis section after OCR completion
- Toggle button to show/hide analysis form
- Integration with job completion callback
- State management for analysis workflow

---

## Documentation

### New Files

#### `LLM_ANALYSIS_GUIDE.md`
Comprehensive guide covering:
- Feature overview and workflow
- Configuration instructions
- API usage examples
- Schema definition guide
- Frontend usage
- Architecture details
- Testing guide
- Best practices
- Troubleshooting
- Future enhancements

#### `.env.example`
Added LLM configuration variables:
```bash
LLM_API_URL="https://api.infomaniak.com/v1/chat/completions"
LLM_API_KEY=""
LLM_MODEL="gpt-3.5-turbo"
LLM_TIMEOUT=60
```

#### `CHANGELOG_LLM_FEATURE.md`
This file - complete changelog of the feature

### Updated Files

#### `README.md`
- Added "Analyse LLM" section to features
- Link to LLM_ANALYSIS_GUIDE.md

---

## Testing

### Test Files

#### `tests/local/test_llm_analysis_example.py`
Example test script demonstrating:
- Invoice extraction example
- Resume/CV extraction example
- Mock service usage
- Schema definition patterns

### Test Strategy

- **Unit Tests**: Use `LLMServiceMock` for fast tests without API calls
- **Integration Tests**: Can use real API with test credentials
- **Mock Service**: Automatically used in test environment

---

## Architecture

### Data Flow

1. **User Input**: Define schema + introduction in frontend
2. **API Request**: POST to `/api/v1/llm/analyze`
3. **Validation**: Backend validates request and retrieves OCR content
4. **Prompt Building**: Optimized prompt with OCR + schema + introduction
5. **LLM Call**: External API call to Infomaniak
6. **Response Parsing**: Extract and validate JSON from LLM response
7. **Storage**: Store result in Redis
8. **Polling**: Frontend polls for status updates
9. **Display**: Show structured data to user

### Service Layer

```
Frontend Component (LLMAnalysis.tsx)
    ↓
API Service (api.ts)
    ↓
API Endpoint (llm_analysis.py)
    ↓
LLM Service (llm_service.py / llm_service_mock.py)
    ↓
External LLM API (Infomaniak)
    ↓
Redis Storage (redis_service.py)
```

### Dependency Injection

- `get_llm_service()`: Singleton LLM service instance
- Uses `@lru_cache()` for single instance across requests
- Cleanup on application shutdown

---

## Configuration Requirements

### Environment Variables

**Required for production:**
```bash
LLM_API_KEY="your_infomaniak_api_key"
```

**Optional (with defaults):**
```bash
LLM_API_URL="https://api.infomaniak.com/v1/chat/completions"
LLM_MODEL="gpt-3.5-turbo"
LLM_TIMEOUT=60
```

### API Key Setup

1. Create Infomaniak account
2. Generate API key with Chat Completions access
3. Add to `.env` file
4. Restart backend service

---

## Usage Examples

### Invoice Extraction

```json
{
  "job_id": "completed-ocr-job-id",
  "introduction": "Extract invoice information including vendor, amounts, and line items",
  "schema": {
    "vendor_name": {
      "type": "string",
      "description": "Company issuing the invoice",
      "required": true
    },
    "total_amount": {
      "type": "number",
      "description": "Total amount due",
      "required": true
    }
  }
}
```

### Resume/CV Extraction

```json
{
  "job_id": "completed-ocr-job-id",
  "introduction": "Extract candidate information from resume",
  "schema": {
    "full_name": {
      "type": "string",
      "description": "Candidate's full name",
      "required": true
    },
    "skills": {
      "type": "array",
      "description": "List of technical skills",
      "required": false
    }
  }
}
```

---

## Performance

### Backend
- **API Call**: 2-10 seconds (depends on LLM model and document size)
- **Retry Logic**: Up to 3 attempts on failure
- **Timeout**: Configurable (default 60s)

### Frontend
- **Polling Interval**: 1 second
- **Max Attempts**: 60 (60 seconds total)
- **UI Updates**: Real-time status updates

---

## Security

### API Key Protection
- Stored in environment variables
- Never exposed to frontend
- Transmitted via secure headers to LLM API

### Input Validation
- Schema validation on backend
- Field type checking
- Required field enforcement
- JSON structure validation

---

## Error Handling

### Backend Errors
- Invalid job ID
- Job not completed
- Empty OCR content
- LLM API failures
- JSON parsing errors
- Schema validation failures

### Frontend Errors
- Missing introduction
- Empty schema
- Invalid field definitions
- Network errors
- Timeout errors

All errors include user-friendly messages and are logged for debugging.

---

## Future Improvements

### Planned Enhancements
1. **Streaming Results**: Real-time partial results
2. **Batch Analysis**: Multiple documents with same schema
3. **Schema Templates**: Pre-defined schemas for common documents
4. **Validation Rules**: Custom validation for extracted data
5. **Multi-language**: Better non-English support
6. **Cost Tracking**: Monitor API usage
7. **Result History**: Compare previous analyses

### Performance Optimizations
1. **Caching**: Cache similar analyses
2. **Prompt Optimization**: Reduce token usage
3. **Model Selection**: Auto-select best model for task
4. **Parallel Processing**: Batch multiple fields

---

## Breaking Changes

None - This is a new feature with no impact on existing functionality.

---

## Migration Guide

No migration needed. The feature is opt-in and doesn't affect existing OCR workflows.

To enable:
1. Add `LLM_API_KEY` to `.env`
2. Restart backend
3. LLM analysis button appears after OCR completion

---

## Contributors

- Implementation: AI Assistant
- Architecture: Following Marker-OCR-API patterns
- Testing: Mock service for fast tests

---

## References

- [Infomaniak API Documentation](https://developer.infomaniak.com/)
- [OpenAI API Format](https://platform.openai.com/docs/api-reference/chat)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)

---

## Support

For issues or questions:
1. Check `LLM_ANALYSIS_GUIDE.md`
2. Verify `.env` configuration
3. Check backend logs
4. Test with mock service first

---

**Version**: 1.1.0  
**Status**: ✅ Complete and Ready for Production  
**Date**: December 16, 2025

