# Backend Tests Structure

This directory contains backend tests organized by test environment type.

## Directory Structure

```
tests/backend/
├── modelFree/          # Tests that run without ML dependencies (fast)
│   ├── file-to-parse/  # Test PDF files
│   ├── test_services/  # Unit tests for services
│   ├── conftest.py     # Pytest configuration
│   └── *.py            # Integration and API tests
└── FullStack/          # Tests that require ML dependencies (slower)
    └── *.py            # Full integration tests with Marker
```

## Test Categories

### `modelFree/` - Tests Without ML Dependencies

These tests can run **quickly** without loading Marker's ML models:

- **Purpose**: Unit tests that don't require ML
- **Execution**: Fast (< 1s startup)
- **Dependencies**: Mock services, no ML models
- **Examples**:
  - `test_services/test_file_handler.py` - File handler unit tests (uses mocks)
  - `test_services/test_serialization.py` - Serialization unit tests (uses mocks)

**Usage**:
```bash
# Run all modelFree tests
make test-backend-modelFree

# Run specific test
make test-url-upload-integration-modelFree

# Run in Docker directly
docker-compose -f docker-compose.test-modelFree.yml run --rm backend-test-modelFree \
  pytest tests/backend/modelFree/ -v
```

### `FullStack/` - Tests With ML Dependencies

These tests require **full Marker ML dependencies**:

- **Purpose**: End-to-end tests with real Marker processing
- **Execution**: Slower (requires ML model loading)
- **Dependencies**: Full Marker library with ML models (no mocks)
- **Examples**:
  - `test_api_url_upload_integration.py` - API integration tests with real Marker processing
  - `file-to-parse/` - Test PDF files for real Marker processing
  - Full document processing tests with actual PDFs

**Usage**:
```bash
# Run all FullStack tests
make test-backend-FullStack

# Run specific test
make test-url-upload-integration-FullStack

# Run in Docker directly
docker-compose -f docker-compose.test-FullStack.yml run --rm backend-test-FullStack \
  pytest tests/backend/FullStack/ -v
```

## Test Files Location

Test PDF files are located in:
- `tests/backend/FullStack/file-to-parse/` - PDFs for FullStack tests (real Marker processing)
  - `exemple_facture.pdf` - Sample invoice PDF
  - `LECLERC.pdf` - Sample LECLERC PDF

## Adding New Tests

### Adding a ModelFree Test

1. Create your test file in `tests/backend/modelFree/`
2. Use mocks for ML dependencies
3. Follow pytest naming conventions (`test_*.py`)
4. Ensure it runs quickly without ML models

### Adding a FullStack Test

1. Create your test file in `tests/backend/FullStack/`
2. Use real Marker services (no mocks)
3. Follow pytest naming conventions (`test_*.py`)
4. Document that it requires ML dependencies

## Best Practices

1. **ModelFree tests** should be fast and not require ML models
2. **FullStack tests** should test real Marker integration
3. Use descriptive names that indicate the test purpose
4. Keep tests focused on a single feature or scenario
5. Document test requirements in docstrings

