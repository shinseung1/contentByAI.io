.PHONY: help install dev build up down logs clean test lint

help: ## Show this help message
	@echo 'Available commands:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e .[dev]

web-install: ## Install web dependencies
	cd web && npm install

dev-setup: ## Setup development environment
	cp .env.example .env
	make install-dev
	make web-install

dev: ## Start development environment
	docker-compose -f docker-compose.dev.yml up --build

build: ## Build Docker images
	docker-compose build

up: ## Start production environment
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs
	docker-compose logs -f

clean: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f

test: ## Run tests
	pytest

lint: ## Run linting
	ruff check .
	mypy .

format: ## Format code
	ruff format .

web-dev: ## Start web development server
	cd web && npm run dev

api-dev: ## Start API development server
	uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

cli: ## Access CLI
	python -m apps.cli.main

backup: ## Create backup of data
	tar -czf backup-$(shell date +%Y%m%d_%H%M%S).tar.gz data/ bundles/ runs/

restore: ## Restore from backup (specify BACKUP_FILE=...)
	tar -xzf $(BACKUP_FILE)

health: ## Check service health
	curl -f http://localhost:8000/api/v1/health/ || echo "Service is down"