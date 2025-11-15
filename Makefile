.PHONY: help build up down logs test clean dev

# Auto-detect container runtime (podman or docker)
CONTAINER_RUNTIME := $(shell command -v podman 2>/dev/null)
ifdef CONTAINER_RUNTIME
    COMPOSE := podman-compose
    RUNTIME_NAME := Podman
else
    CONTAINER_RUNTIME := $(shell command -v docker 2>/dev/null)
    COMPOSE := docker-compose
    RUNTIME_NAME := Docker
endif

help:
	@echo "capa-server - Makefile commands"
	@echo ""
	@echo "Detected runtime: $(RUNTIME_NAME)"
	@echo ""
	@echo "  make build    - Build container image"
	@echo "  make up       - Start the service"
	@echo "  make down     - Stop the service"
	@echo "  make logs     - View logs"
	@echo "  make test     - Test API endpoints"
	@echo "  make clean    - Clean up containers and data"
	@echo "  make dev      - Run development server (no container)"
	@echo ""

build:
	@echo "Building with $(RUNTIME_NAME)..."
	$(COMPOSE) build

up:
	@echo "Starting capa-server with $(RUNTIME_NAME)..."
	$(COMPOSE) up -d
	@echo ""
	@echo "✓ capa-server is starting..."
	@echo "  Web UI:   http://localhost:8080"
	@echo "  API docs: http://localhost:8080/docs"
	@echo ""
	@echo "Run 'make logs' to view output"

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

test:
	@echo "Testing API endpoints..."
	@echo ""
	@curl -f http://localhost:8080/health 2>/dev/null && echo "✓ Health check passed" || echo "✗ Service not responding"
	@echo ""
	@curl -s http://localhost:8080/api/info 2>/dev/null | python3 -m json.tool || echo "✗ API not responding"

clean:
	@echo "Cleaning up..."
	$(COMPOSE) down -v
	rm -rf data/
	@echo "✓ Cleaned up containers and data"

dev:
	@echo "Starting development server..."
	@echo "Make sure you have installed dependencies: pip install -r requirements.txt"
	@echo ""
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
