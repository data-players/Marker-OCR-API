#!/bin/bash
# Quick test script for LLM analysis feature
# This script demonstrates the complete workflow

set -e

API_URL="${API_URL:-http://localhost:8000}"
BASE_URL="$API_URL/api/v1"

echo "🧪 Quick LLM Analysis Test"
echo "=========================="
echo ""
echo "API URL: $BASE_URL"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if test PDF exists
if [ ! -f "tests/backend/FullStack/test_document.pdf" ]; then
    echo "❌ Test PDF not found. Please ensure tests/backend/FullStack/test_document.pdf exists."
    exit 1
fi

echo "${BLUE}Step 1: Upload test document${NC}"
echo "------------------------------"
UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/documents/upload" \
    -F "file=@tests/backend/FullStack/test_document.pdf")

FILE_ID=$(echo $UPLOAD_RESPONSE | grep -o '"file_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$FILE_ID" ]; then
    echo "❌ Upload failed"
    echo "$UPLOAD_RESPONSE"
    exit 1
fi

echo "${GREEN}✓ File uploaded: $FILE_ID${NC}"
echo ""

echo "${BLUE}Step 2: Process document with OCR${NC}"
echo "-----------------------------------"
PROCESS_RESPONSE=$(curl -s -X POST "$BASE_URL/documents/process" \
    -F "file_id=$FILE_ID" \
    -F "output_format=markdown" \
    -F "force_ocr=false" \
    -F "extract_images=false")

JOB_ID=$(echo $PROCESS_RESPONSE | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$JOB_ID" ]; then
    echo "❌ Processing failed"
    echo "$PROCESS_RESPONSE"
    exit 1
fi

echo "${GREEN}✓ Processing started: $JOB_ID${NC}"
echo ""

echo "${YELLOW}⏳ Waiting for OCR to complete...${NC}"
STATUS="pending"
ATTEMPTS=0
MAX_ATTEMPTS=60

while [ "$STATUS" != "completed" ] && [ "$STATUS" != "failed" ] && [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    sleep 2
    STATUS_RESPONSE=$(curl -s "$BASE_URL/documents/jobs/$JOB_ID")
    STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
    ATTEMPTS=$((ATTEMPTS + 1))
    echo -n "."
done

echo ""

if [ "$STATUS" != "completed" ]; then
    echo "❌ OCR processing failed or timed out"
    echo "$STATUS_RESPONSE"
    exit 1
fi

echo "${GREEN}✓ OCR completed${NC}"
echo ""

echo "${BLUE}Step 3: Start LLM analysis${NC}"
echo "---------------------------"

# Create analysis request
ANALYSIS_REQUEST=$(cat <<EOF
{
  "job_id": "$JOB_ID",
  "introduction": "Extract key information from this document. Focus on identifying any names, dates, and important numbers.",
  "schema": {
    "document_type": {
      "type": "string",
      "description": "Type of document (e.g., invoice, contract, report)",
      "required": false
    },
    "key_dates": {
      "type": "array",
      "description": "Important dates mentioned in the document",
      "required": false
    },
    "main_topics": {
      "type": "array",
      "description": "Main topics or subjects discussed in the document",
      "required": false
    }
  }
}
EOF
)

ANALYSIS_RESPONSE=$(curl -s -X POST "$BASE_URL/llm/analyze" \
    -H "Content-Type: application/json" \
    -d "$ANALYSIS_REQUEST")

ANALYSIS_ID=$(echo $ANALYSIS_RESPONSE | grep -o '"analysis_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ANALYSIS_ID" ]; then
    echo "❌ LLM analysis failed to start"
    echo "$ANALYSIS_RESPONSE"
    exit 1
fi

echo "${GREEN}✓ LLM analysis started: $ANALYSIS_ID${NC}"
echo ""

echo "${YELLOW}⏳ Waiting for LLM analysis to complete...${NC}"
ANALYSIS_STATUS="processing"
ATTEMPTS=0
MAX_ATTEMPTS=30

while [ "$ANALYSIS_STATUS" != "completed" ] && [ "$ANALYSIS_STATUS" != "failed" ] && [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    sleep 2
    ANALYSIS_STATUS_RESPONSE=$(curl -s "$BASE_URL/llm/analyze/$ANALYSIS_ID")
    ANALYSIS_STATUS=$(echo $ANALYSIS_STATUS_RESPONSE | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
    ATTEMPTS=$((ATTEMPTS + 1))
    echo -n "."
done

echo ""

if [ "$ANALYSIS_STATUS" != "completed" ]; then
    echo "❌ LLM analysis failed or timed out"
    echo "$ANALYSIS_STATUS_RESPONSE"
    exit 1
fi

echo "${GREEN}✓ LLM analysis completed${NC}"
echo ""

echo "${BLUE}Step 4: Display results${NC}"
echo "------------------------"
echo "$ANALYSIS_STATUS_RESPONSE" | python3 -m json.tool
echo ""

echo "${GREEN}✅ Test completed successfully!${NC}"
echo ""
echo "Summary:"
echo "  - File ID: $FILE_ID"
echo "  - Job ID: $JOB_ID"
echo "  - Analysis ID: $ANALYSIS_ID"
echo ""
echo "You can view the results in the frontend at:"
echo "  http://localhost:3000"

