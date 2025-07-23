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
COMPOSE_FILE := docker-compose.yml
BACKEND_DIR := backend
FRONTEND_DIR := frontend
TEST_RESULTS_DIR := test-results

##@ Application Management

help: ## Display this help message
	@echo "$(BOLD)Marker OCR API - Docker Development Commands$(NC)"
	@echo ""
	@echo "$(BOLD)All environments use Docker containers:$(NC)"
	@echo "  $(YELLOW)dev$(NC)        - Hot reloading with volume mounting"
	@echo "  $(YELLOW)test$(NC)       - Lightweight containers for fast testing"
	@echo "  $(YELLOW)production$(NC) - Optimized containers for deployment"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BOLD)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

setup: setup-docker ## Initial setup - create directories and build Docker images

setup-docker: ## Setup with Docker (recommended)
	@echo "$(BLUE)Setting up project with Docker...$(NC)"
	@mkdir -p shared/uploads shared/outputs $(TEST_RESULTS_DIR)
	@echo "$(GREEN)✓ Directories created$(NC)"
	@echo "$(BLUE)Building development images...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile dev build
	@echo "$(GREEN)✓ Development images built$(NC)"
	@echo "$(BLUE)Building test images...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile test build
	@echo "$(GREEN)✓ Test images built$(NC)"
	@echo "$(GREEN)✓ Project setup complete$(NC)"

##@ Development Environment (Docker with Hot Reloading)

dev: ## Start development environment with hot reloading (Docker)
	@echo "$(BLUE)Starting development environment with hot reloading...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile dev up -d
	@echo "$(GREEN)✓ Development environment started$(NC)"
	@echo "$(YELLOW)Frontend:$(NC) http://localhost:3000 (hot reloading)"
	@echo "$(YELLOW)Backend API:$(NC) http://localhost:8000 (hot reloading)"
	@echo "$(YELLOW)API Docs:$(NC) http://localhost:8000/docs"
	@echo "$(YELLOW)Redis:$(NC) localhost:6379"

dev-build: ## Build and start development environment
	@echo "$(BLUE)Building and starting development environment...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile dev up -d --build
	@echo "$(GREEN)✓ Development environment built and started$(NC)"

dev-backend: ## Start only backend in development mode (Docker)
	@echo "$(BLUE)Starting backend development server with hot reloading...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile dev up -d redis backend-dev
	@echo "$(GREEN)✓ Backend development server started$(NC)"
	@echo "$(YELLOW)Backend API:$(NC) http://localhost:8000 (hot reloading)"
	@echo "$(YELLOW)API Docs:$(NC) http://localhost:8000/docs"

dev-frontend: ## Start only frontend in development mode (Docker)
	@echo "$(BLUE)Starting frontend development server with hot reloading...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile dev up -d frontend-dev
	@echo "$(GREEN)✓ Frontend development server started$(NC)"
	@echo "$(YELLOW)Frontend:$(NC) http://localhost:3000 (hot reloading)"

dev-logs: ## Show development logs
	@docker-compose -f $(COMPOSE_FILE) --profile dev logs -f

dev-logs-backend: ## Show backend development logs
	@docker-compose -f $(COMPOSE_FILE) --profile dev logs -f backend-dev

dev-logs-frontend: ## Show frontend development logs
	@docker-compose -f $(COMPOSE_FILE) --profile dev logs -f frontend-dev

dev-down: ## Stop development environment
	@echo "$(BLUE)Stopping development environment...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile dev down
	@echo "$(GREEN)✓ Development environment stopped$(NC)"

dev-restart: dev-down dev ## Restart development environment

##@ Production Environment (Docker)

prod: ## Start production environment (Docker)
	@echo "$(BLUE)Starting production environment...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile production up -d
	@echo "$(GREEN)✓ Production environment started$(NC)"
	@echo "$(YELLOW)Frontend:$(NC) http://localhost (port 80)"
	@echo "$(YELLOW)Backend API:$(NC) http://localhost:8000"
	@echo "$(YELLOW)API Docs:$(NC) http://localhost:8000/docs"

prod-build: ## Build and start production environment
	@echo "$(BLUE)Building and starting production environment...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile production up -d --build
	@echo "$(GREEN)✓ Production environment built and started$(NC)"

prod-down: ## Stop production environment
	@echo "$(BLUE)Stopping production environment...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile production down
	@echo "$(GREEN)✓ Production environment stopped$(NC)"

prod-logs: ## Show production logs
	@docker-compose -f $(COMPOSE_FILE) --profile production logs -f

##@ Testing (Docker)

test: ## Run all tests (backend + frontend) in Docker containers
	@echo "$(BLUE)Running all tests in Docker containers...$(NC)"
	@$(MAKE) test-backend-fast
	@$(MAKE) test-frontend-docker
	@echo "$(GREEN)✓ All tests completed$(NC)"

test-backend: test-backend-fast ## Run backend tests in Docker (alias)

test-backend-fast: ## Run backend tests with lightweight container (< 1s)
	@echo "$(BLUE)Running backend tests with lightweight container...$(NC)"
	@mkdir -p $(TEST_RESULTS_DIR)
	@docker-compose --profile test -f $(COMPOSE_FILE) run --rm backend-test
	@echo "$(GREEN)✓ Backend tests completed$(NC)"

test-backend-fast-report: ## Run backend tests with coverage reports
	@echo "$(BLUE)Running backend tests with coverage reports...$(NC)"
	@mkdir -p $(TEST_RESULTS_DIR)/backend-coverage
	@docker-compose --profile test -f $(COMPOSE_FILE) run --rm \
		-v ./$(TEST_RESULTS_DIR)/backend-coverage:/app/htmlcov \
		backend-test pytest --cov=app --cov-report=html --cov-report=xml
	@echo "$(GREEN)✓ Backend tests with reports completed$(NC)"
	@echo "$(YELLOW)Coverage report:$(NC) $(TEST_RESULTS_DIR)/backend-coverage/index.html"

test-frontend: test-frontend-docker ## Run frontend tests in Docker (alias)

test-frontend-docker: ## Run frontend tests in Docker container
	@echo "$(BLUE)Running frontend tests in Docker...$(NC)"
	@mkdir -p $(TEST_RESULTS_DIR)
	@docker-compose --profile test -f $(COMPOSE_FILE) run --rm frontend-test
	@echo "$(GREEN)✓ Frontend tests completed$(NC)"

test-watch-backend: ## Run backend tests in watch mode (Docker)
	@echo "$(BLUE)Running backend tests in watch mode (Docker)...$(NC)"
	@docker-compose --profile test -f $(COMPOSE_FILE) run --rm backend-test pytest --watch

test-watch-frontend: ## Run frontend tests in watch mode (Docker)
	@echo "$(BLUE)Running frontend tests in watch mode (Docker)...$(NC)"
	@docker-compose --profile test -f $(COMPOSE_FILE) run --rm frontend-test npm run test:watch

##@ Building Images

build: ## Build all Docker images (dev, test, production)
	@echo "$(BLUE)Building all Docker images...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile dev --profile test --profile production build
	@echo "$(GREEN)✓ All images built successfully$(NC)"

build-dev: ## Build development images
	@echo "$(BLUE)Building development images...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile dev build
	@echo "$(GREEN)✓ Development images built$(NC)"

build-test: ## Build test images
	@echo "$(BLUE)Building test images...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile test build
	@echo "$(GREEN)✓ Test images built$(NC)"

build-prod: ## Build production images
	@echo "$(BLUE)Building production images...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile production build
	@echo "$(GREEN)✓ Production images built$(NC)"

build-backend-dev: ## Build backend development image
	@echo "$(BLUE)Building backend development image...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile dev build backend-dev
	@echo "$(GREEN)✓ Backend development image built$(NC)"

build-frontend-dev: ## Build frontend development image
	@echo "$(BLUE)Building frontend development image...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile dev build frontend-dev
	@echo "$(GREEN)✓ Frontend development image built$(NC)"

build-backend-test: ## Build lightweight backend test image
	@echo "$(BLUE)Building backend test image...$(NC)"
	@docker-compose --profile test -f $(COMPOSE_FILE) build backend-test
	@echo "$(GREEN)✓ Backend test image built$(NC)"

##@ Utilities and Monitoring

down: ## Stop all services (all profiles)
	@echo "$(BLUE)Stopping all services...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) --profile dev --profile test --profile production down
	@echo "$(GREEN)✓ All services stopped$(NC)"

logs: ## Show logs for all active services
	@docker-compose -f $(COMPOSE_FILE) logs -f

status: ## Show status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	@docker-compose -f $(COMPOSE_FILE) ps -a

health: ## Check health of all services
	@echo "$(BLUE)Health Check:$(NC)"
	@docker-compose -f $(COMPOSE_FILE) ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

shell-backend-dev: ## Open shell in backend development container
	@docker-compose -f $(COMPOSE_FILE) --profile dev exec backend-dev bash

shell-frontend-dev: ## Open shell in frontend development container
	@docker-compose -f $(COMPOSE_FILE) --profile dev exec frontend-dev sh

shell-redis: ## Open Redis CLI
	@docker-compose -f $(COMPOSE_FILE) exec redis redis-cli

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
		docker-compose -f $(COMPOSE_FILE) --profile dev --profile test --profile production down -v; \
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
	@docker-compose -f $(COMPOSE_FILE) up -d redis
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
	@cd $(BACKEND_DIR) && pip install -r requirements.txt
	@echo "$(GREEN)✓ Backend dependencies installed locally$(NC)"
	@cd $(FRONTEND_DIR) && npm install
	@echo "$(GREEN)✓ Frontend dependencies installed locally$(NC)"
	@echo "$(GREEN)✓ Local project setup complete$(NC)" 