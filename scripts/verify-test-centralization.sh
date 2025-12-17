#!/bin/bash
# Verify that ALL tests are centralized in tests/ directory
# This script should be run in CI/CD to enforce test centralization

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Centralization Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Find all test files outside tests/ directory
echo -e "${YELLOW}Searching for test files outside tests/ directory...${NC}"
echo ""

VIOLATIONS_FOUND=0

# Search patterns for test files
PATTERNS=(
    "test_*.py"
    "*_test.py"
    "*.test.js"
    "*.test.jsx"
    "*.test.ts"
    "*.test.tsx"
    "*.spec.js"
    "*.spec.jsx"
    "*.spec.ts"
    "*.spec.tsx"
)

for pattern in "${PATTERNS[@]}"; do
    # Find files matching pattern, excluding tests/, node_modules/, .git/, etc.
    FILES=$(find . -name "$pattern" \
        ! -path "*/tests/*" \
        ! -path "*/node_modules/*" \
        ! -path "*/.git/*" \
        ! -path "*/__pycache__/*" \
        ! -path "*/venv/*" \
        ! -path "*/.venv/*" \
        ! -path "*/dist/*" \
        ! -path "*/build/*" \
        ! -path "*/coverage/*" \
        2>/dev/null || true)
    
    if [ -n "$FILES" ]; then
        echo -e "${RED}✗ Found test files outside tests/ matching pattern: $pattern${NC}"
        echo "$FILES" | while read -r file; do
            echo -e "  ${RED}$file${NC}"
        done
        echo ""
        VIOLATIONS_FOUND=$((VIOLATIONS_FOUND + 1))
    fi
done

# Check for common test directories outside tests/
FORBIDDEN_DIRS=(
    "backend/tests"
    "backend/test"
    "frontend/tests"
    "frontend/test"
    "frontend/src/__tests__"
    "tests/local"
)

echo -e "${YELLOW}Checking for forbidden test directories...${NC}"
echo ""

for dir in "${FORBIDDEN_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${RED}✗ Found forbidden test directory: $dir${NC}"
        VIOLATIONS_FOUND=$((VIOLATIONS_FOUND + 1))
    fi
done

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Verification Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ $VIOLATIONS_FOUND -eq 0 ]; then
    echo -e "${GREEN}✓ All tests are properly centralized in tests/ directory${NC}"
    echo ""
    echo -e "${GREEN}Test structure:${NC}"
    echo -e "${GREEN}  tests/backend/modelFree/ - Unit tests${NC}"
    echo -e "${GREEN}  tests/backend/FullStack/ - Integration tests${NC}"
    echo -e "${GREEN}  tests/frontend/         - Frontend tests${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Found $VIOLATIONS_FOUND violation(s)${NC}"
    echo ""
    echo -e "${YELLOW}Action required:${NC}"
    echo -e "  1. Move test files to appropriate directory in tests/"
    echo -e "  2. Update imports if necessary"
    echo -e "  3. Update test configuration (jest.config.js, pytest.ini)"
    echo -e "  4. Delete original files"
    echo -e "  5. Run tests to verify: make test"
    echo ""
    echo -e "${YELLOW}See .cursorrules-tests for detailed rules${NC}"
    echo ""
    exit 1
fi

