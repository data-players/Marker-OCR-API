# Marker OCR API - Makefile
# Provides commands to run the application and tests at different levels with Docker
# All environments (dev, test, prod) use Docker containers
# Author: Development Team
# Last Updated: $(date)

.PHONY: help build up down logs clean test test-backend test-frontend dev setup
.DEFAULT_GOAL := help

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
BOLD = \033[1m
NC = \033[0m # No Color

# Configuration
COMPOSE_FILE_DEV := docker-compose.dev.yml
COMPOSE_FILE_TEST_MODELFREE := docker-compose.test-modelFree.yml
COMPOSE_FILE_TEST_FULLSTACK := docker-compose.test-FullStack.yml
BACKEND_DIR := backend
FRONTEND_DIR := frontend
TEST_RESULTS_DIR := test-results

##@ Application Management

help: ## Display this help message
	@echo "$(BOLD)Marker OCR API - Docker Development Commands$(NC)"
	@echo ""
	@echo "$(BOLD)Available Docker environments:$(NC)"
	@echo "  $(YELLOW)dev$(NC)              - Hot reloading with volume mounting (docker-compose.dev.yml)"
	@echo "  $(YELLOW)test-modelFree$(NC)   - Lightweight containers without ML dependencies (docker-compose.test-modelFree.yml)"
	@echo "  $(YELLOW)test-FullStack$(NC)   - Full test environment with ML dependencies (docker-compose.test-FullStack.yml)"
	@echo ""
	@echo "$(BOLD)Note:$(NC) Production deployment is managed in Marker-OCR-API-prod repository"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(YELLOW)%-35s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BOLD)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

setup: setup-docker ## Initial setup - create directories and build Docker images

setup-docker: ## Setup with Docker (recommended)
	@echo "$(BLUE)Setting up project with Docker...$(NC)"
	@mkdir -p shared/uploads shared/outputs $(TEST_RESULTS_DIR)
	@echo "$(GREEN)✓ Directories created$(NC)"
	@echo "$(BLUE)Building development images...$(NC)"
	@docker compose -f $(COMPOSE_FILE_DEV) build
	@echo "$(GREEN)✓ Development images built$(NC)"
	@echo "$(BLUE)Building test images...$(NC)"
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) build
	@echo "$(GREEN)✓ Test images built$(NC)"
	@echo "$(GREEN)✓ Project setup complete$(NC)"

##@ Development Environment (Docker with Hot Reloading)

dev: ## Start development environment with hot reloading (Docker)
	@echo "$(BLUE)Starting development environment with hot reloading...$(NC)"
	@docker compose -f $(COMPOSE_FILE_DEV) up -d
	@echo "$(GREEN)✓ Development environment started$(NC)"
	@echo "$(YELLOW)Frontend:$(NC) http://localhost:3000 (hot reloading)"
	@echo "$(YELLOW)Backend API:$(NC) http://localhost:8000 (hot reloading)"
	@echo "$(YELLOW)API Docs:$(NC) http://localhost:8000/docs"
	@echo "$(YELLOW)Redis:$(NC) localhost:6379"

dev-build: ## Build and start development environment
	@echo "$(BLUE)Building and starting development environment...$(NC)"
	@docker compose -f $(COMPOSE_FILE_DEV) up -d --build
	@echo "$(GREEN)✓ Development environment built and started$(NC)"

dev-backend: ## Start only backend in development mode (Docker)
	@echo "$(BLUE)Starting backend development server with hot reloading...$(NC)"
	@docker compose -f $(COMPOSE_FILE_DEV) up -d redis backend-dev
	@echo "$(GREEN)✓ Backend development server started$(NC)"
	@echo "$(YELLOW)Backend API:$(NC) http://localhost:8000 (hot reloading)"
	@echo "$(YELLOW)API Docs:$(NC) http://localhost:8000/docs"

dev-frontend: ## Start only frontend in development mode (Docker)
	@echo "$(BLUE)Starting frontend development server with hot reloading...$(NC)"
	@docker compose -f $(COMPOSE_FILE_DEV) up -d frontend-dev
	@echo "$(GREEN)✓ Frontend development server started$(NC)"
	@echo "$(YELLOW)Frontend:$(NC) http://localhost:3000 (hot reloading)"

dev-logs: ## Show development logs
	@docker compose -f $(COMPOSE_FILE_DEV) logs -f

dev-logs-backend: ## Show backend development logs
	@docker compose -f $(COMPOSE_FILE_DEV) logs -f backend-dev

dev-logs-frontend: ## Show frontend development logs
	@docker compose -f $(COMPOSE_FILE_DEV) logs -f frontend-dev

dev-down: ## Stop development environment
	@echo "$(BLUE)Stopping development environment...$(NC)"
	@docker compose -f $(COMPOSE_FILE_DEV) down
	@echo "$(GREEN)✓ Development environment stopped$(NC)"

dev-restart: dev-down dev ## Restart development environment

##@ Production Environment (Docker)
# Note: Production deployment is managed in Marker-OCR-API-prod repository

prod: ## [NOT AVAILABLE] Production managed in separate repository (Marker-OCR-API-prod)
	@echo "$(YELLOW)⚠️  Production environment is managed in Marker-OCR-API-prod repository$(NC)"
	@echo "$(BLUE)This development repository does not include production configuration$(NC)"

prod-build: ## [NOT AVAILABLE] Production managed in separate repository (Marker-OCR-API-prod)
	@echo "$(YELLOW)⚠️  Production environment is managed in Marker-OCR-API-prod repository$(NC)"
	@echo "$(BLUE)This development repository does not include production configuration$(NC)"

prod-down: ## [NOT AVAILABLE] Production managed in separate repository (Marker-OCR-API-prod)
	@echo "$(YELLOW)⚠️  Production environment is managed in Marker-OCR-API-prod repository$(NC)"
	@echo "$(BLUE)This development repository does not include production configuration$(NC)"

prod-logs: ## [NOT AVAILABLE] Production managed in separate repository (Marker-OCR-API-prod)
	@echo "$(YELLOW)⚠️  Production environment is managed in Marker-OCR-API-prod repository$(NC)"
	@echo "$(BLUE)This development repository does not include production configuration$(NC)"

##@ Testing (Docker)

test: ## Run all tests (backend + frontend) in Docker containers
	@echo "$(BLUE)Running all tests in Docker containers...$(NC)"
	@$(MAKE) test-backend-fast
	@$(MAKE) test-frontend-docker
	@echo "$(GREEN)✓ All tests completed$(NC)"

test-backend: test-backend-fast ## Run backend tests in Docker (alias)

test-backend-fast: test-backend-modelFree ## Run backend tests with lightweight container (< 1s) (alias)

test-backend-modelFree: ## Run backend tests with modelFree container (without ML dependencies)
	@echo "$(BLUE)Running backend tests (modelFree) with modelFree container...$(NC)"
	@mkdir -p $(TEST_RESULTS_DIR)
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) run --rm \
		backend-test-modelFree pytest tests/backend/modelFree --tb=short -v
	@echo "$(GREEN)✓ Backend tests (modelFree) completed$(NC)"

test-url-upload-integration: test-url-upload-integration-modelFree ## Run URL upload integration test (alias)

test-url-upload-integration-modelFree: ## Run URL upload integration test with modelFree container (requires API running) - DEPRECATED: use FullStack
	@echo "$(YELLOW)⚠ This test requires Marker and should use FullStack. Redirecting to FullStack...$(NC)"
	@$(MAKE) test-url-upload-integration-FullStack

test-url-upload-integration-FullStack: ## Run URL upload integration test with FullStack container (requires API running)
	@echo "$(BLUE)Running URL upload integration test (FullStack)...$(NC)"
	@echo "$(YELLOW)Note: This test requires the API to be running (make dev-backend)$(NC)"
	@mkdir -p $(TEST_RESULTS_DIR)
	@docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) run --rm \
		-e API_BASE_URL=http://host.docker.internal:8000 \
		backend-test-FullStack pytest tests/backend/FullStack/test_api_url_upload_integration.py -v
	@echo "$(GREEN)✓ URL upload integration test with FullStack completed$(NC)"

test-backend-fast-report: test-backend-modelFree-report ## Run backend tests with coverage reports (alias)

test-backend-modelFree-report: ## Run backend tests with coverage reports (modelFree)
	@echo "$(BLUE)Running backend tests with coverage reports (modelFree)...$(NC)"
	@mkdir -p $(TEST_RESULTS_DIR)/backend-coverage
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) run --rm \
		-v ./$(TEST_RESULTS_DIR)/backend-coverage:/app/htmlcov \
		backend-test-modelFree pytest tests/backend/modelFree --cov=app --cov-report=html --cov-report=xml
	@echo "$(GREEN)✓ Backend tests with reports completed$(NC)"
	@echo "$(YELLOW)Coverage report:$(NC) $(TEST_RESULTS_DIR)/backend-coverage/index.html"

test-frontend: test-frontend-docker ## Run frontend tests in Docker (alias)

test-frontend-docker: ## Run frontend tests in Docker container
	@echo "$(BLUE)Running frontend tests in Docker...$(NC)"
	@mkdir -p $(TEST_RESULTS_DIR)
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) run --rm frontend-test
	@echo "$(GREEN)✓ Frontend tests completed$(NC)"

test-watch-backend: test-watch-backend-modelFree ## Run backend tests in watch mode (alias)

test-watch-backend-modelFree: ## Run backend tests in watch mode (modelFree)
	@echo "$(BLUE)Running backend tests in watch mode (modelFree)...$(NC)"
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) run --rm backend-test-modelFree pytest tests/backend/modelFree --watch

test-watch-frontend: ## Run frontend tests in watch mode (Docker)
	@echo "$(BLUE)Running frontend tests in watch mode (Docker)...$(NC)"
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) run --rm frontend-test npm run test:watch

test-local: ## List and run local development tests (manual/script tests)
	@echo "$(BLUE)Local Development Tests$(NC)"
	@echo "$(YELLOW)These are manual/development tests, not CI tests$(NC)"
	@echo ""
	@if [ -d "tests/local" ] && [ -n "$$(ls -A tests/local/*.py 2>/dev/null)" ]; then \
		echo "$(GREEN)Available local tests:$(NC)"; \
		ls -1 tests/local/*.py 2>/dev/null | sed 's|tests/local/|  - |' | sed 's|\.py$$||'; \
		echo ""; \
		echo "$(YELLOW)Run individual tests with:$(NC)"; \
		echo "  python tests/local/test_<name>.py"; \
		echo ""; \
		echo "$(YELLOW)Or in Docker:$(NC)"; \
		echo "  docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) run --rm backend-test-FullStack \\"; \
		echo "    python /app/../tests/local/test_<name>.py"; \
	else \
		echo "$(YELLOW)No local tests found in tests/local/$(NC)"; \
	fi

test-FullStack: test-FullStack-run ## Test Marker with FullStack container (alias)

test-FullStack-run: ## Test Marker with FullStack container (requires ML dependencies)
	@echo "$(BLUE)Testing Marker with FullStack container...$(NC)"
	@./tests/local/test-real-pdf.sh test

test-FullStack-build: ## Build FullStack test image with ML dependencies
	@echo "$(BLUE)Building FullStack test image...$(NC)"
	@./tests/local/test-real-pdf.sh build

test-FullStack-shell: ## Open shell in FullStack test container
	@echo "$(BLUE)Opening shell in FullStack test container...$(NC)"
	@./tests/local/test-real-pdf.sh shell

test-FullStack-logs: ## View logs from FullStack test container
	@echo "$(BLUE)Viewing FullStack test logs...$(NC)"
	@./tests/local/test-real-pdf.sh logs

test-FullStack-stop: ## Stop FullStack test services
	@echo "$(BLUE)Stopping FullStack test services...$(NC)"
	@./tests/local/test-real-pdf.sh stop

# Legacy aliases for backward compatibility
test-real-pdf: test-FullStack-run ## Test Marker with real PDF files (legacy alias)
test-real-pdf-build: test-FullStack-build ## Build test image (legacy alias)
test-real-pdf-shell: test-FullStack-shell ## Open shell (legacy alias)
test-real-pdf-logs: test-FullStack-logs ## View logs (legacy alias)
test-real-pdf-stop: test-FullStack-stop ## Stop services (legacy alias)

##@ Building Images

build: ## Build all Docker images (dev and test)
	@echo "$(BLUE)Building all Docker images...$(NC)"
	@docker compose -f $(COMPOSE_FILE_DEV) build
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) build
	@docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) build
	@echo "$(GREEN)✓ All images built successfully$(NC)"

build-dev: ## Build development images
	@echo "$(BLUE)Building development images...$(NC)"
	@docker compose -f $(COMPOSE_FILE_DEV) build
	@echo "$(GREEN)✓ Development images built$(NC)"

build-test: ## Build test images (modelFree and FullStack)
	@echo "$(BLUE)Building test images...$(NC)"
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) build
	@docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) build
	@echo "$(GREEN)✓ Test images built$(NC)"

build-test-modelFree: ## Build modelFree test images
	@echo "$(BLUE)Building modelFree test images...$(NC)"
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) build
	@echo "$(GREEN)✓ ModelFree test images built$(NC)"

build-test-FullStack: ## Build FullStack test images
	@echo "$(BLUE)Building FullStack test images...$(NC)"
	@docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) build
	@echo "$(GREEN)✓ FullStack test images built$(NC)"

build-backend-dev: ## Build backend development image
	@echo "$(BLUE)Building backend development image...$(NC)"
	@docker compose -f $(COMPOSE_FILE_DEV) build backend-dev
	@echo "$(GREEN)✓ Backend development image built$(NC)"

build-frontend-dev: ## Build frontend development image
	@echo "$(BLUE)Building frontend development image...$(NC)"
	@docker compose -f $(COMPOSE_FILE_DEV) build frontend-dev
	@echo "$(GREEN)✓ Frontend development image built$(NC)"

build-backend-test: build-test-modelFree ## Build lightweight backend test image (alias)

build-backend-test-modelFree: ## Build modelFree backend test image
	@echo "$(BLUE)Building backend test image (modelFree)...$(NC)"
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) build backend-test-modelFree
	@echo "$(GREEN)✓ Backend test image (modelFree) built$(NC)"

build-backend-test-FullStack: ## Build FullStack backend test image
	@echo "$(BLUE)Building backend test image (FullStack)...$(NC)"
	@docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) build backend-test-FullStack
	@echo "$(GREEN)✓ Backend test image (FullStack) built$(NC)"

##@ Utilities and Monitoring

down: ## Stop all services (dev and test)
	@echo "$(BLUE)Stopping all services...$(NC)"
	@docker compose -f $(COMPOSE_FILE_DEV) down 2>/dev/null || true
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) down 2>/dev/null || true
	@docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) down 2>/dev/null || true
	@echo "$(GREEN)✓ All services stopped$(NC)"

logs: ## Show logs for development services
	@docker compose -f $(COMPOSE_FILE_DEV) logs -f

status: ## Show status of all services
	@echo "$(BLUE)Development Services:$(NC)"
	@docker compose -f $(COMPOSE_FILE_DEV) ps -a 2>/dev/null || echo "No dev services running"
	@echo ""
	@echo "$(BLUE)Test Services (modelFree):$(NC)"
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) ps -a 2>/dev/null || echo "No modelFree test services running"
	@echo ""
	@echo "$(BLUE)Test Services (FullStack):$(NC)"
	@docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) ps -a 2>/dev/null || echo "No FullStack test services running"

health: ## Check health of development services
	@echo "$(BLUE)Health Check (Development):$(NC)"
	@docker compose -f $(COMPOSE_FILE_DEV) ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No services running"

shell-backend-dev: ## Open shell in backend development container
	@docker compose -f $(COMPOSE_FILE_DEV) exec backend-dev bash

shell-frontend-dev: ## Open shell in frontend development container
	@docker compose -f $(COMPOSE_FILE_DEV) exec frontend-dev sh

shell-redis: ## Open Redis CLI
	@docker compose -f $(COMPOSE_FILE_DEV) exec redis redis-cli

##@ Cleanup

clean: ## Remove stopped containers and unused images
	@echo "$(BLUE)Cleaning up Docker resources...$(NC)"
	@docker system prune -f
	@echo "$(GREEN)✓ Cleanup completed$(NC)"

clean-all: ## Remove all Docker resources (containers, images, volumes)
	@echo "$(BLUE)Removing all Docker resources...$(NC)"
	@echo "$(RED)Warning: This will remove all Docker images and volumes!$(NC)"
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose -f $(COMPOSE_FILE_DEV) down -v 2>/dev/null || true; \
		docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) down -v 2>/dev/null || true; \
		docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) down -v 2>/dev/null || true; \
		docker system prune -a -f --volumes; \
		echo "$(GREEN)✓ All Docker resources removed$(NC)"; \
	else \
		echo "$(YELLOW)Cleanup cancelled$(NC)"; \
	fi

clean-test: ## Remove test result files
	@echo "$(BLUE)Cleaning test results...$(NC)"
	@rm -rf $(TEST_RESULTS_DIR)
	@mkdir -p $(TEST_RESULTS_DIR)
	@echo "$(GREEN)✓ Test results cleaned$(NC)"

##@ Legacy Local Commands (Deprecated)

dev-local: ## [DEPRECATED] Start development environment locally (requires Python & Node.js)
	@echo "$(YELLOW)⚠️  This command is deprecated. Use 'make dev' for Docker development instead.$(NC)"
	@echo "$(BLUE)Starting development environment locally...$(NC)"
	@echo "$(YELLOW)Starting Redis...$(NC)"
	@docker compose -f $(COMPOSE_FILE_DEV) up -d redis
	@echo "$(YELLOW)Starting backend locally...$(NC)"
	@cd $(BACKEND_DIR) && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "$(YELLOW)Starting frontend locally...$(NC)"
	@cd $(FRONTEND_DIR) && npm run dev &
	@echo "$(GREEN)✓ Local development environment started$(NC)"

setup-local: ## [DEPRECATED] Setup with local dependencies (requires Python & Node.js)
	@echo "$(YELLOW)⚠️  This command is deprecated. Use 'make setup' for Docker setup instead.$(NC)"
	@echo "$(BLUE)Setting up project locally...$(NC)"
	@mkdir -p shared/uploads shared/outputs $(TEST_RESULTS_DIR)
	@echo "$(GREEN)✓ Directories created$(NC)"
	@cd $(BACKEND_DIR) && pip install -r requirements-models.txt && pip install -r requirements-minimal.txt && pip install -r requirements-base.txt
	@echo "$(GREEN)✓ Backend dependencies installed locally$(NC)"
	@cd $(FRONTEND_DIR) && npm install
	@echo "$(GREEN)✓ Frontend dependencies installed locally$(NC)"
	@echo "$(GREEN)✓ Local project setup complete$(NC)" 