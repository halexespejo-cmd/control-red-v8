.PHONY: help install test run format lint clean docker-build docker-up docker-down

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	cd backend && python -m venv venv
	cd backend && . venv/bin/activate && pip install --upgrade pip
	cd backend && . venv/bin/activate && pip install -r requirements.txt
	cd backend && . venv/bin/activate && pip install pytest-cov black flake8 isort
	@echo "✅ Dependencies installed"

test: ## Run tests with coverage
	cd backend && . venv/bin/activate && pytest src/tests/ -v --cov=src --cov-report=term-missing

test-fast: ## Run tests without coverage
	cd backend && . venv/bin/activate && pytest src/tests/ -v

run: ## Run backend server
	cd backend && . venv/bin/activate && python -m src.main

run-dev: ## Run backend with reload
	cd backend && . venv/bin/activate && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

celery-worker: ## Run Celery worker
	cd backend && . venv/bin/activate && celery -A src.celery_app worker --loglevel=info

celery-beat: ## Run Celery beat (periodic tasks)
	cd backend && . venv/bin/activate && celery -A src.celery_app beat --loglevel=info

celery-flower: ## Run Flower (Celery monitoring UI)
	cd backend && . venv/bin/activate && celery -A src.celery_app flower --port=5555

format: ## Format code with black and isort
	cd backend && . venv/bin/activate && black src/
	cd backend && . venv/bin/activate && isort --profile black src/
	@echo "✅ Code formatted"

lint: ## Lint code with flake8
	cd backend && . venv/bin/activate && flake8 src/ --max-line-length=120 --extend-ignore=E203,W503

check: format lint test ## Format, lint and test

clean: ## Clean cache and temporary files
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name 'htmlcov' -exec rm -rf {} +
	find . -type f -name '.coverage' -delete
	rm -rf backend/*.db
	@echo "✅ Cleaned"

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start containers
	docker-compose up -d
	@echo "✅ Containers started"
	@echo "Backend: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"

docker-down: ## Stop containers
	docker-compose down

docker-logs: ## Show container logs
	docker-compose logs -f backend

docker-shell: ## Open shell in backend container
	docker-compose exec backend /bin/bash

version: ## Show version
	@cat VERSION
