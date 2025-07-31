# Multi-Tenant RAG System - Development Makefile

.PHONY: help install dev-setup start stop logs clean test lint format build deploy

# Default target
help:
	@echo "Multi-Tenant RAG System - Available Commands:"
	@echo ""
	@echo "Setup Commands:"
	@echo "  install       Install Python dependencies"
	@echo "  dev-setup     Setup development environment"
	@echo ""
	@echo "Development Commands:"
	@echo "  start         Start all services with Docker Compose"
	@echo "  stop          Stop all services"
	@echo "  restart       Restart all services"
	@echo "  logs          Show logs from all services"
	@echo "  logs-backend  Show backend logs only"
	@echo "  logs-frontend Show frontend logs only"
	@echo ""
	@echo "Database Commands:"
	@echo "  db-start      Start only database services"
	@echo "  db-reset      Reset database (WARNING: destroys data)"
	@echo "  setup-data    Setup sample data"
	@echo ""
	@echo "Quality Commands:"
	@echo "  test          Run all tests"
	@echo "  test-cov      Run tests with coverage"
	@echo "  lint          Run linting"
	@echo "  format        Format code"
	@echo "  type-check    Run type checking"
	@echo ""
	@echo "Build Commands:"
	@echo "  build         Build Docker images"
	@echo "  build-no-cache Build Docker images without cache"
	@echo ""
	@echo "Maintenance Commands:"
	@echo "  clean         Clean up Docker resources"
	@echo "  clean-all     Clean everything including volumes"
	@echo "  health        Check system health"

# Installation
install:
	pip install -r requirements.txt

dev-setup: install
	@echo "Setting up development environment..."
	cp env.example .env
	@echo "Please edit .env file with your configuration"

# Service Management
start:
	docker-compose up -d
	@echo "Services starting... Check status with 'make logs'"

stop:
	docker-compose down

restart: stop start

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

# Database Management
db-start:
	docker-compose up -d postgres redis qdrant

db-reset:
	@echo "WARNING: This will destroy all data. Press Ctrl+C to cancel."
	@sleep 5
	docker-compose down -v
	docker-compose up -d postgres redis qdrant
	@echo "Database reset complete"

setup-data:
	python scripts/setup_sample_data.py

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term

test-api:
	pytest tests/test_api.py -v

# Code Quality
lint:
	flake8 app/ tests/
	black --check app/ tests/
	isort --check-only app/ tests/

format:
	black app/ tests/
	isort app/ tests/

type-check:
	mypy app/

# Build
build:
	docker-compose build

build-no-cache:
	docker-compose build --no-cache

# Maintenance
clean:
	docker-compose down --rmi local --remove-orphans

clean-all:
	docker-compose down -v --rmi all --remove-orphans
	docker system prune -f

health:
	@echo "Checking system health..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "Backend not responding"
	@curl -s http://localhost:8501/_stcore/health > /dev/null && echo "Frontend: healthy" || echo "Frontend: not responding"

# Development server (local)
dev-backend:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	streamlit run frontend/streamlit_app.py --server.port 8501

# Production
deploy-prod:
	@echo "Production deployment not implemented yet"
	@echo "Configure your production environment first"

# Quick development cycle
quick-start: db-start
	@echo "Starting databases only for local development"
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals"

# Environment check
check-env:
	@echo "Checking environment..."
	@python -c "import sys; print(f'Python: {sys.version}')"
	@docker --version
	@docker-compose --version

# Documentation
docs:
	@echo "Opening documentation..."
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Frontend: http://localhost:8501"
	@echo "README: see README.md"

# Shortcuts
up: start
down: stop
rebuild: clean build start