# Tests Directory Structure

This directory contains **all tests** for the Marker OCR API project, organized by component (backend/frontend) and type (local/permanent).

## Directory Structure

```
tests/
├── backend/          # Backend tests (pytest)
│   ├── file-to-parse/  # Test PDF files
│   ├── test_services/  # Unit tests for services
│   └── *.py           # Integration and API tests
├── frontend/         # Frontend tests (Jest)
│   └── src/          # Component tests
└── local/            # Local/development test scripts
    ├── *.py          # Manual test scripts
    └── *.sh          # Test helper scripts
```

## Tests Categories

### `backend/` - Backend Tests (Pytest)

These are **automated pytest tests** for the backend API:

- **Purpose**: Unit tests, integration tests, API tests
- **Execution**: Run via pytest in Docker containers
- **Structure**: Mirrors backend application structure
- **Examples**:
  - `test_api_url_upload_integration.py` - Integration tests for URL upload
  - `test_services/test_file_handler.py` - Unit tests for file handler
  - `test_services/test_serialization.py` - Unit tests for serialization

**Test Files Location**: `tests/backend/file-to-parse/`
- `exemple_facture.pdf` - Sample invoice PDF
- `LECLERC.pdf` - Sample LECLERC PDF

**Usage**:
```bash
# Run all backend tests (modelFree - without ML dependencies)
make test-backend-modelFree

# Run all backend tests (FullStack - with ML dependencies)
make test-backend-FullStack

# Run specific test (modelFree)
make test-url-upload-integration-modelFree

# Run specific test (FullStack)
make test-url-upload-integration-FullStack

# Run in Docker directly (modelFree)
docker-compose -f docker-compose.test-modelFree.yml run --rm backend-test-modelFree \
  pytest tests/backend/ -v

# Run in Docker directly (FullStack)
docker-compose -f docker-compose.test-FullStack.yml run --rm backend-test-FullStack \
  pytest tests/backend/ -v
```

### `frontend/` - Frontend Tests (Jest)

These are **automated Jest tests** for the frontend React application:

- **Purpose**: Component tests, integration tests
- **Execution**: Run via Jest/npm test
- **Structure**: Mirrors frontend src structure
- **Examples**:
  - `src/App.test.tsx` - App component tests
  - `src/App.test.jsx` - App component tests (legacy)

**Usage**:
```bash
# Run frontend tests
make test-frontend

# Run in Docker
docker-compose -f docker-compose.test-modelFree.yml run --rm frontend-test
```

### `local/` - Local/Development Tests

These are **development and debugging scripts** that are run manually:

- **Purpose**: Quick tests, debugging, manual verification
- **Execution**: Run directly on host machine or in Docker containers
- **Examples**:
  - `test_marker_logs.py` - Test Marker log capture
  - `test_url_upload.py` - Manual URL upload testing
  - `test_api_substeps.py` - Verify API sub-steps
  - `test_sse_frontend.py` - Test SSE frontend integration
  - `test-real-pdf.sh` - Script to test with real PDFs

**Usage**:
```bash
# Run locally
python tests/local/test_marker_logs.py

# Run in Docker (FullStack)
docker-compose -f docker-compose.test-FullStack.yml run --rm backend-test-FullStack \
  python /app/../tests/local/test_marker_logs.py
```

## Test Environments

### ModelFree (Lightweight)

- **Docker Compose**: `docker-compose.test-modelFree.yml`
- **Dockerfile**: `backend/Dockerfile.test-modelFree`
- **Service**: `backend-test-modelFree`
- **Characteristics**: Fast, without ML dependencies
- **Use Case**: Unit tests, API tests, quick validation

### FullStack (Complete)

- **Docker Compose**: `docker-compose.test-FullStack.yml`
- **Dockerfile**: `backend/Dockerfile.test-FullStack`
- **Service**: `backend-test-FullStack`
- **Characteristics**: Slow, with all ML dependencies
- **Use Case**: Integration tests with real Marker processing

## Adding New Tests

### Adding a Backend Test

1. Create your test file in `tests/backend/` following pytest conventions
2. Use descriptive names: `test_<feature>_<purpose>.py`
3. Follow the existing structure (e.g., `test_services/` for service tests)
4. Ensure it follows pytest naming conventions (`test_*.py`)

### Adding a Frontend Test

1. Create your test file in `tests/frontend/src/` following Jest conventions
2. Use descriptive names: `<Component>.test.tsx` or `<Component>.test.jsx`
3. Mirror the structure of `frontend/src/`

### Adding a Local Test Script

1. Create your test script in `tests/local/`
2. Add a descriptive name: `test_<feature>_<purpose>.py` or `.sh`
3. Document usage in the script header

## Best Practices

1. **Backend tests** should be idempotent and follow pytest conventions
2. **Frontend tests** should be component-focused and follow Jest conventions
3. **Local tests** should be self-contained scripts that can run independently
4. Use descriptive names that indicate the test purpose
5. Document test requirements and setup in script headers
6. Keep tests focused on a single feature or scenario
7. **All tests must be in `tests/` directory** - no tests outside this directory

## Migration Notes

- **Old location**: `backend/tests/` → **New location**: `tests/backend/`
- **Old location**: `test/file-to-parse/` → **New location**: `tests/backend/file-to-parse/`
- **Old location**: `frontend/src/*.test.*` → **New location**: `tests/frontend/src/*.test.*`
- **Removed**: `tests/permanent/` (was a mirror, no longer needed)
