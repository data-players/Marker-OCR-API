# Marker OCR API - Makefile
# Development & Testing Commands
# Production deployment: see Marker-OCR-API-prod repository
# Author: Development Team
# Last Updated: 2024-12-17

.PHONY: help setup build start stop test clean
.DEFAULT_GOAL := help

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
BOLD = \033[1m
NC = \033[0m # No Color

# Configuration
COMPOSE_FILE := docker-compose.dev.yml
COMPOSE_FILE_TEST_MODELFREE := docker-compose.test-modelFree.yml
COMPOSE_FILE_TEST_FULLSTACK := docker-compose.test-FullStack.yml
TEST_RESULTS_DIR := test-results

##@ Help

help: ## Display this help message
	@echo "$(BOLD)Marker OCR API - Development & Testing$(NC)"
	@echo ""
	@echo "$(BLUE)Note: Production managed in Marker-OCR-API-prod repository$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(YELLOW)%-30s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BOLD)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup & Build

setup: ## Initial setup - create directories and build all images
	@echo "$(BLUE)Setting up project...$(NC)"
	@mkdir -p shared/uploads shared/outputs $(TEST_RESULTS_DIR)
	@echo "$(GREEN)✓ Directories created$(NC)"
	@$(MAKE) build
	@echo "$(GREEN)✓ Project setup complete$(NC)"

build: ## Build all Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	@docker compose -f $(COMPOSE_FILE) build
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) build
	@docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) build
	@echo "$(GREEN)✓ All images built$(NC)"

build-test: ## Build test images only (modelFree + FullStack)
	@echo "$(BLUE)Building test images...$(NC)"
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) build
	@docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) build
	@echo "$(GREEN)✓ Test images built$(NC)"

##@ Development

start: ## Start development environment (hot reloading)
	@echo "$(BLUE)Starting development environment...$(NC)"
	@docker compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✓ Development environment started$(NC)"
	@echo ""
	@echo "$(YELLOW)Services:$(NC)"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo "  Redis:     localhost:6379"
	@echo ""
	@echo "$(YELLOW)Commands:$(NC)"
	@echo "  make stop        - Stop all services"
	@echo "  make logs        - View logs"
	@echo "  make restart     - Restart environment"

up: start ## Alias for start

backend: ## Start backend only (with Redis)
	@echo "$(BLUE)Starting backend...$(NC)"
	@docker compose -f $(COMPOSE_FILE) up -d redis backend-dev
	@echo "$(GREEN)✓ Backend started: http://localhost:8000$(NC)"

frontend: ## Start frontend only
	@echo "$(BLUE)Starting frontend...$(NC)"
	@docker compose -f $(COMPOSE_FILE) up -d frontend-dev
	@echo "$(GREEN)✓ Frontend started: http://localhost:3000$(NC)"

restart: stop start ## Restart development environment

logs: ## Show logs (all services)
	@docker compose -f $(COMPOSE_FILE) logs -f

logs-backend: ## Show backend logs only
	@docker compose -f $(COMPOSE_FILE) logs -f backend-dev

logs-frontend: ## Show frontend logs only
	@docker compose -f $(COMPOSE_FILE) logs -f frontend-dev

##@ Stop

stop: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(NC)"
	@docker compose -f $(COMPOSE_FILE) down 2>/dev/null || true
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) down 2>/dev/null || true
	@docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) down 2>/dev/null || true
	@echo "$(GREEN)✓ All services stopped$(NC)"

down: stop ## Alias for stop

##@ Testing

test: ## Run all tests (modelFree + FullStack + frontend)
	@echo "$(BOLD)$(BLUE)========================================$(NC)"
	@echo "$(BOLD)$(BLUE)MARKER OCR API - TEST SUITE$(NC)"
	@echo "$(BOLD)$(BLUE)========================================$(NC)"
	@echo ""
	@$(MAKE) test-unit || exit 1
	@echo ""
	@$(MAKE) test-integration || exit 1
	@echo ""
	@$(MAKE) test-frontend || exit 1
	@echo ""
	@echo "$(BOLD)$(BLUE)========================================$(NC)"
	@echo "$(BOLD)$(GREEN)✓ ALL TESTS PASSED!$(NC)"
	@echo "$(BOLD)$(BLUE)========================================$(NC)"

test-quick: ## Run quick tests only (unit + frontend)
	@echo "$(BLUE)Running quick tests...$(NC)"
	@$(MAKE) test-unit
	@$(MAKE) test-frontend
	@echo "$(GREEN)✓ Quick tests completed$(NC)"

test-unit: ## Run unit tests (fast, no ML)
	@echo "$(BLUE)Running unit tests...$(NC)"
	@mkdir -p $(TEST_RESULTS_DIR)
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) run --rm \
		backend-test-modelfree pytest /tests/backend/modelFree --tb=short -v
	@echo "$(GREEN)✓ Unit tests completed$(NC)"

test-integration: ## Run integration tests (with ML)
	@echo "$(BLUE)Running integration tests...$(NC)"
	@mkdir -p $(TEST_RESULTS_DIR)
	@docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) run --rm \
		backend-test-fullstack pytest /tests/backend/FullStack --tb=short -v
	@echo "$(GREEN)✓ Integration tests completed$(NC)"

test-frontend: ## Run frontend tests (Jest)
	@echo "$(BLUE)Running frontend tests...$(NC)"
	@mkdir -p $(TEST_RESULTS_DIR)
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) run --rm frontend-test
	@echo "$(GREEN)✓ Frontend tests completed$(NC)"

test-marks: ## Show available pytest marks
	@echo "$(BOLD)$(BLUE)Pytest Marks$(NC)"
	@echo ""
	@echo "$(YELLOW)Available marks:$(NC)"
	@echo "  $(GREEN)unit$(NC)          - Fast unit tests (< 100ms)"
	@echo "  $(GREEN)integration$(NC)   - Integration tests"
	@echo "  $(GREEN)api$(NC)           - API endpoint tests"
	@echo "  $(GREEN)ml$(NC)            - Tests requiring ML models"
	@echo "  $(GREEN)slow$(NC)          - Slow tests (> 5s)"
	@echo "  $(GREEN)modelfree$(NC)     - Without ML dependencies"
	@echo "  $(GREEN)fullstack$(NC)     - With full ML stack"
	@echo ""
	@echo "$(YELLOW)Usage:$(NC)"
	@echo "  make test-mark MARK=unit"
	@echo "  make test-mark MARK=integration"
	@echo "  make test-mark MARK=ml"

test-mark: ## Run tests by mark (usage: make test-mark MARK=unit)
	@if [ -z "$(MARK)" ]; then \
		echo "$(RED)Error: MARK parameter required$(NC)"; \
		echo "$(YELLOW)Usage: make test-mark MARK=unit$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Running tests with mark: $(MARK)$(NC)"
	@if echo "$(MARK)" | grep -qE '(ml|integration|fullstack)'; then \
		docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) run --rm \
			backend-test-fullstack pytest -m "$(MARK)" -v; \
	else \
		docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) run --rm \
			backend-test-modelfree pytest -m "$(MARK)" -v; \
	fi

verify-tests: ## Verify test centralization
	@echo "$(BLUE)Verifying test centralization...$(NC)"
	@./scripts/verify-test-centralization.sh
	@echo "$(GREEN)✓ Test centralization verified$(NC)"

##@ Cleanup

clean: ## Remove stopped containers and unused images
	@echo "$(BLUE)Cleaning Docker resources...$(NC)"
	@docker system prune -f
	@echo "$(GREEN)✓ Cleanup completed$(NC)"

clean-all: ## Remove all Docker resources (WARNING: destructive)
	@echo "$(RED)WARNING: This will remove all Docker images and volumes!$(NC)"
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose -f $(COMPOSE_FILE) down -v 2>/dev/null || true; \
		docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) down -v 2>/dev/null || true; \
		docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) down -v 2>/dev/null || true; \
		docker system prune -a -f --volumes; \
		echo "$(GREEN)✓ All resources removed$(NC)"; \
	else \
		echo "$(YELLOW)Cleanup cancelled$(NC)"; \
	fi

clean-tests: ## Remove test result files
	@echo "$(BLUE)Cleaning test results...$(NC)"
	@rm -rf $(TEST_RESULTS_DIR)
	@mkdir -p $(TEST_RESULTS_DIR)
	@echo "$(GREEN)✓ Test results cleaned$(NC)"

##@ Utilities

status: ## Show status of all services
	@echo "$(BLUE)Services Status:$(NC)"
	@docker compose -f $(COMPOSE_FILE) ps 2>/dev/null || echo "  No services running"
	@echo ""
	@echo "$(BLUE)Test Services:$(NC)"
	@docker compose -f $(COMPOSE_FILE_TEST_MODELFREE) ps 2>/dev/null || echo "  No services running"
	@docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) ps 2>/dev/null || echo "  No services running"

shell-backend: ## Open shell in backend container
	@docker compose -f $(COMPOSE_FILE) exec backend-dev bash

shell-test: ## Open shell in test container (FullStack)
	@docker compose -f $(COMPOSE_FILE_TEST_FULLSTACK) run --rm backend-test-fullstack bash

ps: status ## Alias for status
