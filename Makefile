.PHONY: help install install-deps test lint format clean clean-all reset-db

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
UV := uv

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; { \
 		printf "\033[36m%-30s\033[0m %s\n", $$1, $$2 \
 	}'
	@echo ''

install: install-deps init-db ## Install and initialize application
	@echo "Installing dependencies..."
	@$(UV) sync
	@echo "✅ Dependencies installed"
	@echo ""
	@echo "Initializing database..."
	@$(MAKE) init-db
	@echo "✅ Database initialized"
	@echo ""
	@echo "✅ Installation complete!"
	@echo ""
	@echo "To start application:"
	@echo "  make dev       (Terminal 1 - FastAPI with auto-reload)"
	@echo "  make run-worker (Terminal 2 - Celery worker)"
	@echo ""
	@echo "For production:"
	@echo "  make run       (Terminal - FastAPI production mode)"

install-deps: ## Install Python dependencies with uv
	@echo "Installing dependencies..."
	@$(UV) sync
	@echo "✅ Dependencies installed"

init-db: ## Initialize database tables
	@echo "Initializing database with Alembic migrations..."
	@$(UV) run alembic upgrade head
	@echo "✅ Database initialized"

reset-db: ## Drop and recreate database tables
	@echo "Resetting database..."
	@$(UV) run alembic downgrade base && $(UV) run alembic upgrade head
	@echo "✅ Database reset"

dev: ## Start FastAPI server in development mode
	@echo "Starting FastAPI server in development mode..."
	@$(UV) run fastapi dev src/main.py --host 0.0.0.0 --port 8000

run: ## Start FastAPI server (production mode)
	@echo "Starting FastAPI server (production)..."
	@$(UV) run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

run-worker: ## Start Celery worker
	@echo "Starting Celery worker..."
	@$(UV) run celery -A src.workers.celery_app worker --loglevel=info

run-worker-debug: ## Start Celery worker (with debug logging)
	@echo "Starting Celery worker (debug)..."
	@$(UV) run celery -A src.workers.celery_app worker --loglevel=debug

dev-all: ## Start API and worker in development mode
	@echo "Starting development environment..."
	@echo "Press Ctrl+C to stop all services"
	@$(MAKE) dev & $(MAKE) run-worker

test: ## Run all tests
	@echo "Running tests..."
	@$(UV) run pytest -v

test-cov: ## Run tests with coverage
	@echo "Running tests with coverage..."
	@$(UV) run pytest --cov=src --cov-report=html --cov-report=term

lint: ## Run linter (ruff)
	@echo "Running linter..."
	@$(UV) run ruff check src/ tests/

lint-fix: ## Fix linting issues automatically
	@echo "Fixing linting issues..."
	@$(UV) run ruff check --fix src/ tests/

format: ## Format code with ruff and sort imports with isort
	@echo "Formatting code..."
	@$(UV) run ruff format src/ tests/
	@$(UV) run isort src/ tests/

format-check: ## Check if code is formatted
	@echo "Checking code format..."
	@$(UV) run ruff format --check src/ tests/
	@$(UV) run isort --check-only src/ tests/

type-check: ## Run type checker
	@echo "Running type checker..."
	@$(UV) run mypy src/

db-migrate: ## Create a new database migration
	@echo "Creating new migration..."
	@read -p "Migration description: " desc; \
 		$(UV) run alembic revision --autogenerate -m "$$desc"

db-upgrade: ## Apply database migrations
	@echo "Applying migrations..."
	@$(UV) run alembic upgrade head

db-downgrade: ## Rollback last database migration
	@echo "Rolling back migration..."
	@$(UV) run alembic downgrade -1

db-history: ## Show migration history
	@$(UV) run alembic history

db-current: ## Show current migration version
	@$(UV) run alembic current

shell: ## Open Python shell with app context
	@$(UV) run python

api-docs: ## Open API documentation
	@echo "Opening API documentation at http://localhost:8000/docs"
	@open http://localhost:8000/docs || echo "Open http://localhost:8000/docs in your browser"

api-redoc: ## Open API ReDoc documentation
	@echo "Opening ReDoc at http://localhost:8000/redoc"
	@open http://localhost:8000/redoc || echo "Open http://localhost:8000/redoc in your browser"

check-api: ## Check if FastAPI is responding
	@echo "Checking FastAPI health..."
	@curl -s http://localhost:8000/health || echo "❌ API not responding"
	@curl -s http://localhost:8000/health && echo "✅ API is healthy"

test-ocr: ## Test OCR functionality
	@echo "Testing OCR functionality..."
	@$(UV) run python -c "from src.services.ocr.factory import get_ocr_provider; from src.core.settings import settings; from src.models.schemas import OCRBoundingBox; import asyncio; async def test_ocr(): provider = get_ocr_provider(); print(f'OCR Provider: {type(provider).__name__}'); print(f'OCR Settings: {settings.use_textract_ocr}'); print(f'Tesseract path: {settings.tesseract_path}'); print('✅ OCR service initialized successfully'); asyncio.run(test_ocr())"
	@echo "✅ OCR test completed"

clean: ## Clean Python cache and temporary files
	@echo "Cleaning Python cache..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name "*.pyc" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type f -name "*.log" -delete
	@echo "✅ Cleaned cache files"
