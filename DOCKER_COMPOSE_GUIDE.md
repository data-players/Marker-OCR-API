# Docker Compose Guide

This guide explains the separation of docker-compose files for different environments.

## Overview

The Marker-OCR-API project uses **separate docker-compose files** for different environments:

```
Marker-OCR-API/
├── docker-compose.dev.yml      ← Development environment
├── docker-compose.test.yml     ← Testing environment
└── (production config in Marker-OCR-API-prod/)

Marker-OCR-API-prod/
└── docker-compose.yml          ← Production environment (with Traefik)
```

## Environments

### Development (`docker-compose.dev.yml`)

**Purpose:** Local development with hot reloading

**Services:**
- `backend-dev`: FastAPI with auto-reload on code changes
- `frontend-dev`: React dev server with hot module replacement
- `redis`: Shared cache service

**Usage:**
```bash
cd Marker-OCR-API

# Start dev environment
docker-compose -f docker-compose.dev.yml up

# Or use make command
make up-dev  # (if configured in Makefile)
```

**Features:**
- ✅ Hot reloading for backend code
- ✅ Hot module replacement for frontend
- ✅ Volume mounts for live development
- ✅ Debug mode enabled
- ✅ Accessible at:
  - Frontend: `http://localhost:3000`
  - Backend: `http://localhost:8000`
  - API Docs: `http://localhost:8000/docs`

### Testing (`docker-compose.test.yml`)

**Purpose:** Run unit and integration tests

**Services:**
- `backend-test`: Run Python tests with minimal dependencies
- `frontend-test`: Run Jest tests with coverage

**Usage:**
```bash
cd Marker-OCR-API

# Run all tests
docker-compose -f docker-compose.test.yml up

# Or specific tests
docker-compose -f docker-compose.test.yml run backend-test pytest
docker-compose -f docker-compose.test.yml run frontend-test npm test
```

**Features:**
- ✅ Lightweight test environment
- ✅ Minimal dependencies (via `Dockerfile.test`)
- ✅ Test coverage reporting
- ✅ Fast build and execution
- ✅ No Redis or other services included

### Production (`../Marker-OCR-API-prod/docker-compose.yml`)

**Purpose:** Production deployment with Traefik reverse proxy

**Services:**
- `traefik`: Reverse proxy with SSL/TLS and load balancing
- `backend`: FastAPI in production mode
- `frontend`: React optimized build
- `redis`: Cache with persistence

**Usage:**
```bash
cd ../Marker-OCR-API-prod

# Setup environment
cp .env.example .env
nano .env  # Configure your domain, email, etc.

# Start services
make up
```

**Features:**
- ✅ Automatic SSL/TLS (Let's Encrypt)
- ✅ HTTP → HTTPS redirect
- ✅ Reverse proxy routing
- ✅ Docker service discovery
- ✅ Logging and monitoring
- ✅ Health checks
- ✅ Accessible at:
  - Frontend: `https://your-domain.com`
  - API: `https://api.your-domain.com`
  - Dashboard: `https://traefik.your-domain.com`

## File Organization

```
backend/
├── Dockerfile        ← Production image
├── Dockerfile.dev    ← Development image
└── Dockerfile.test   ← Test image

frontend/
├── Dockerfile        ← Production image
├── Dockerfile.dev    ← Development image
└── (uses target: test in docker-compose.test.yml)
```

## Key Differences

| Aspect | Dev | Test | Production |
|--------|-----|------|-----------|
| Hot Reload | ✅ Yes | ❌ No | ❌ No |
| Redis | ✅ Yes | ❌ No | ✅ Yes |
| Traefik | ❌ No | ❌ No | ✅ Yes |
| Port 80/443 | ❌ No | ❌ No | ✅ Yes |
| SSL/TLS | ❌ No | ❌ No | ✅ Auto |
| Health Checks | ❌ No | ❌ No | ✅ Yes |
| Debug Mode | ✅ Yes | ✅ Debug | ❌ No |
| Logging | Console | Console | JSON file |
| Restarts | Manual | One-shot | Unless-stopped |

## Usage Examples

### Development Workflow

```bash
cd Marker-OCR-API

# Start dev environment
docker-compose -f docker-compose.dev.yml up

# Access services
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# Docs: http://localhost:8000/docs

# Stop when done
docker-compose -f docker-compose.dev.yml down
```

### Testing

```bash
cd Marker-OCR-API

# Run all tests
docker-compose -f docker-compose.test.yml up

# Run specific test service
docker-compose -f docker-compose.test.yml run backend-test pytest app/

# Run with specific options
docker-compose -f docker-compose.test.yml run backend-test pytest --cov app/
```

### Production Deployment

```bash
cd ../Marker-OCR-API-prod

# Setup
cp .env.example .env
nano .env

# Initialize Traefik
bash init-traefik.sh

# Deploy
make build
make up

# Monitor
make logs-traefik
make status
```

## Adding New Make Targets

For the main project, you can add helper targets in the Makefile:

```makefile
up-dev: ## Start development environment
	docker-compose -f docker-compose.dev.yml up

down-dev: ## Stop development environment
	docker-compose -f docker-compose.dev.yml down

test: ## Run tests
	docker-compose -f docker-compose.test.yml up

test-backend: ## Run backend tests only
	docker-compose -f docker-compose.test.yml run backend-test pytest

test-frontend: ## Run frontend tests only
	docker-compose -f docker-compose.test.yml run frontend-test npm test
```

## Environment Variables

Each docker-compose file can define different environment variables for its services.

**Development (.env.dev):**
```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

**Testing (.env.test):**
```env
ENVIRONMENT=test
LOG_LEVEL=DEBUG
```

**Production (.env in Marker-OCR-API-prod/):**
```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
DOMAIN=your-domain.com
```

## Network Isolation

All services use the `marker-network` Docker network, ensuring:
- ✅ Services can communicate with each other
- ✅ Isolated from other Docker networks
- ✅ Services referenced by name (e.g., `redis://redis:6379`)
- ✅ Clean separation between environments

## Volume Management

### Development
- Source code mounted for hot reload
- Temporary files excluded (node_modules, __pycache__)

### Testing
- Minimal volumes (only test artifacts)
- Fast startup and cleanup

### Production
- Named volumes for persistence
- Data survives container restarts
- Backup-friendly locations

## Troubleshooting

### Development Issues

```bash
# Check service status
docker-compose -f docker-compose.dev.yml ps

# View logs
docker-compose -f docker-compose.dev.yml logs -f backend-dev

# Restart services
docker-compose -f docker-compose.dev.yml restart
```

### Test Issues

```bash
# Run tests with verbose output
docker-compose -f docker-compose.test.yml run backend-test pytest -v

# Run specific test file
docker-compose -f docker-compose.test.yml run backend-test pytest tests/test_services/
```

## Migration Between Environments

```bash
# Stop current environment
docker-compose -f docker-compose.dev.yml down

# Switch to production
cd ../Marker-OCR-API-prod
make up

# Data persists in Docker volumes
```

## Next Steps

- **Development**: See backend/Dockerfile.dev and frontend/Dockerfile.dev
- **Testing**: See backend/Dockerfile.test and test configuration
- **Production**: See ../Marker-OCR-API-prod/README.md and MIGRATION_GUIDE.md



