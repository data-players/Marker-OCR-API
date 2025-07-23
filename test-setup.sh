#!/bin/bash

# Test setup script for Marker OCR API
# This script tests if Docker-based tests work correctly

set -e

echo "🧪 Testing Marker OCR API Setup"
echo "================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if make command exists
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
if ! command -v make &> /dev/null; then
    echo -e "${RED}❌ make command not found. Please install make.${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ docker command not found. Please install Docker.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose command not found. Please install Docker Compose.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Test 2: Setup project
echo -e "${YELLOW}🔧 Setting up project...${NC}"
make setup

# Test 3: Build images
echo -e "${YELLOW}🏗️  Building Docker images...${NC}"
make build

# Test 4: Test backend (minimal test)
echo -e "${YELLOW}🧪 Running backend tests...${NC}"
if make test-backend-docker; then
    echo -e "${GREEN}✅ Backend tests passed${NC}"
else
    echo -e "${RED}❌ Backend tests failed${NC}"
    exit 1
fi

# Test 5: Test frontend (minimal test)
echo -e "${YELLOW}🎨 Running frontend tests...${NC}"
if make test-frontend-docker; then
    echo -e "${GREEN}✅ Frontend tests passed${NC}"
else
    echo -e "${RED}❌ Frontend tests failed${NC}"
    exit 1
fi

# Test 6: Start application briefly
echo -e "${YELLOW}🚀 Testing application startup...${NC}"
make up -d
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Application started successfully${NC}"
    make down
else
    echo -e "${RED}❌ Application failed to start${NC}"
    make down
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 All tests passed! Your setup is working correctly.${NC}"
echo ""
echo "Next steps:"
echo "  • Run: make up-build     # Start the full application"
echo "  • Run: make test         # Run all tests"
echo "  • Run: make help         # See all available commands"
echo ""
echo "Access points:"
echo "  • Frontend:  http://localhost:3000"
echo "  • Backend:   http://localhost:8000"
echo "  • API Docs:  http://localhost:8000/docs" 