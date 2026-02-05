# =============================================================================
# DocuMind Makefile
# =============================================================================
# Usage: make <target>
# Run 'make help' to see all available commands
# =============================================================================

.PHONY: help install dev run test lint format clean docker-up docker-down

help:
	@echo "DocuMind Development Commands"
	@echo "=============================="
	@echo ""
	@echo "Setup:"
	@echo "  make install     - Install all dependencies"
	@echo "  make dev         - Install dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make run         - Run the FastAPI server"
	@echo "  make worker      - Run Celery worker"
	@echo "  make test        - Run all tests"
	@echo "  make lint        - Run linter"
	@echo "  make format      - Format code"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up   - Start all services"
	@echo "  make docker-down - Stop all services"
	@echo ""
	@echo "Database:"
	@echo "  make db-upgrade  - Apply migrations"

install:
	pip install -r backend/requirements.txt

dev: install
	pip install -r backend/requirements-dev.txt

run:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	cd backend && celery -A workers.celery_app worker --loglevel=info

test:
	cd backend && pytest

lint:
	ruff check backend/

format:
	ruff format backend/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

db-upgrade:
	cd backend && alembic upgrade head

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
