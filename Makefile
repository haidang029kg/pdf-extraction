.PHONY: help install install-deps start-services stop-services restart-services init-localstack init-db run-api run-worker run-beat test lint format clean clean-all reset-db

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
UV := uv
APP_NAME := freight_audit

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; { \
		printf "\033[36m%-30s\033[0m %s\n", $$1, $$2 \
	}'
	@echo ''

install: install-deps init-localstack init-db ## Install and initialize everything
	@echo "Installing dependencies..."
	@$(UV) sync
	@echo "✅ Dependencies installed"
	@echo ""
	@echo "Starting services..."
	@$(MAKE) start-services
	@sleep 10
	@echo ""
	@echo "Initializing LocalStack..."
	@$(MAKE) init-localstack
	@echo ""
	@echo "Initializing database..."
	@$(MAKE) init-db
	@echo ""
	@echo "✅ Installation complete!"
	@echo ""
	@echo "To start the application:"
	@echo "  make run-api    (Terminal 1)"
	@echo "  make run-worker (Terminal 2)"

install-deps: ## Install Python dependencies with uv
	@echo "Installing dependencies..."
	@$(UV) sync
	@echo "✅ Dependencies installed"

start-services: ## Start external services (PostgreSQL, Redis, LocalStack)
	@echo "Starting external services..."
	@docker-compose -f docker-compose.services.yml up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	@echo "✅ Services started"
	@docker-compose -f docker-compose.services.yml ps

stop-services: ## Stop external services
	@echo "Stopping external services..."
	@docker-compose -f docker-compose.services.yml down
	@echo "✅ Services stopped"

restart-services: ## Restart external services
	@echo "Restarting external services..."
	@$(MAKE) stop-services
	@sleep 2
	@$(MAKE) start-services

services-logs: ## Show logs from all services
	@docker-compose -f docker-compose.services.yml logs -f

services-ps: ## Show status of all services
	@docker-compose -f docker-compose.services.yml ps

init-localstack: ## Initialize LocalStack S3 bucket
	@echo "Initializing LocalStack S3 bucket..."
	@$(UV) run python scripts/setup_localstack.py
	@echo "✅ LocalStack initialized"

init-db: ## Initialize database tables
	@echo "Initializing database..."
	@$(UV) run python scripts/init_db.py
	@echo "✅ Database initialized"

reset-db: ## Drop and recreate database tables
	@echo "Resetting database..."
	@$(UV) run python -c "from app.db.session import init_db; init_db()"
	@echo "✅ Database reset"

run-api: ## Start FastAPI server (with auto-reload)
	@echo "Starting FastAPI server..."
	@$(UV) run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-api-prod: ## Start FastAPI server (production mode)
	@echo "Starting FastAPI server (production)..."
	@$(UV) run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

run-worker: ## Start Celery worker
	@echo "Starting Celery worker..."
	@$(UV) run celery -A app.workers.celery_app worker --loglevel=info

run-worker-debug: ## Start Celery worker (with debug logging)
	@echo "Starting Celery worker (debug)..."
	@$(UV) run celery -A app.workers.celery_app worker --loglevel=debug

run-beat: ## Start Celery beat scheduler
	@echo "Starting Celery beat scheduler..."
	@$(UV) run celery -A app.workers.celery_app beat --loglevel=info

dev: ## Start API and worker in development mode
	@echo "Starting development environment..."
	@echo "Press Ctrl+C to stop all services"
	@$(MAKE) run-api & $(MAKE) run-worker

test: ## Run all tests
	@echo "Running tests..."
	@$(UV) run pytest -v

test-cov: ## Run tests with coverage
	@echo "Running tests with coverage..."
	@$(UV) run pytest --cov=app --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode
	@echo "Running tests in watch mode..."
	@$(UV) run pytest-watch -v

lint: ## Run linter (ruff)
	@echo "Running linter..."
	@$(UV) run ruff check app/ tests/

lint-fix: ## Fix linting issues automatically
	@echo "Fixing linting issues..."
	@$(UV) run ruff check --fix app/ tests/

format: ## Format code with ruff
	@echo "Formatting code..."
	@$(UV) run ruff format app/ tests/

format-check: ## Check if code is formatted
	@echo "Checking code format..."
	@$(UV) run ruff format --check app/ tests/

type-check: ## Run type checker
	@echo "Running type checker..."
	@$(UV) run mypy app/

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

check-services: ## Check if all services are running
	@echo "Checking service status..."
	@echo ""
	@echo "PostgreSQL:"
	@docker ps | grep freight_audit_postgres || echo "❌ Not running"
	@docker ps | grep freight_audit_postgres && echo "✅ Running"
	@echo ""
	@echo "Redis:"
	@docker ps | grep freight_audit_redis || echo "❌ Not running"
	@docker ps | grep freight_audit_redis && echo "✅ Running"
	@echo ""
	@echo "LocalStack:"
	@docker ps | grep freight_audit_localstack || echo "❌ Not running"
	@docker ps | grep freight_audit_localstack && echo "✅ Running"

check-api: ## Check if FastAPI is responding
	@echo "Checking FastAPI health..."
	@curl -s http://localhost:8000/health || echo "❌ API not responding"
	@curl -s http://localhost:8000/health && echo "✅ API is healthy"

check-redis: ## Check Redis connection
	@echo "Checking Redis connection..."
	@$(UV) run python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping() and print('✅ Redis connected') or print('❌ Redis connection failed')"

check-db: ## Check PostgreSQL connection
	@echo "Checking PostgreSQL connection..."
	@$(UV) run python -c "import psycopg2; conn = psycopg2.connect('postgresql://freight_audit:your_password@localhost:5432/freight_audit'); print('✅ PostgreSQL connected') or print('❌ PostgreSQL connection failed')"

check-localstack: ## Check LocalStack connection
	@echo "Checking LocalStack connection..."
	@curl -s http://localhost:4566/health && echo "✅ LocalStack is healthy" || echo "❌ LocalStack not responding"

logs-api: ## Show API logs (if running in Docker)
	@docker logs freight_extractor_app || echo "API not running in Docker"

logs-worker: ## Show worker logs (if running in Docker)
	@docker logs freight_extractor_worker || echo "Worker not running in Docker"

clean: ## Clean Python cache and temporary files
	@echo "Cleaning Python cache..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name "*.pyc" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type f -name "*.log" -delete
	@echo "✅ Cleaned cache files"

clean-all: clean clean-docker clean-volumes ## Clean everything (cache, Docker, volumes)
	@echo "Cleaning everything..."

clean-docker: ## Stop and remove Docker containers
	@echo "Stopping and removing Docker containers..."
	@docker stop freight_audit_postgres freight_audit_redis freight_audit_localstack 2>/dev/null || true
	@docker rm freight_audit_postgres freight_audit_redis freight_audit_localstack 2>/dev/null || true
	@echo "✅ Docker containers removed"

clean-volumes: ## Remove Docker volumes (⚠️ deletes data)
	@echo "Removing Docker volumes..."
	@docker volume rm pdf-extract_postgres_data pdf-extract_redis_data pdf-extract_localstack_data 2>/dev/null || true
	@echo "✅ Docker volumes removed"

psql-shell: ## Open PostgreSQL shell
	@docker exec -it freight_audit_postgres psql -U freight_audit -d freight_audit

redis-shell: ## Open Redis CLI
	@docker exec -it freight_audit_redis redis-cli

docker-build: ## Build Docker image for application
	@echo "Building Docker image..."
	@docker build -t freight_invoice_extractor .
	@echo "✅ Docker image built"

docker-run: ## Run application in Docker
	@echo "Running application in Docker..."
	@docker run --name freight_extractor_app \
		-p 8000:8000 \
		--env-file .env \
		--link freight_audit_postgres:postgres \
		--link freight_audit_redis:redis \
		--link freight_audit_localstack:localstack \
		-d freight_invoice_extractor
	@echo "✅ Application running in Docker"

docker-stop: ## Stop application running in Docker
	@docker stop freight_extractor_app || true
	@docker rm freight_extractor_app || true
	@echo "✅ Application stopped"

setup-dev: ## Quick setup for development
	@$(MAKE) install-deps
	@echo ""
	@$(MAKE) start-services
	@echo ""
	@echo "Waiting for services..."
	@sleep 10
	@$(MAKE) init-localstack
	@$(MAKE) init-db
	@echo ""
	@echo "✅ Development setup complete!"
	@echo ""
	@echo "Run 'make dev' to start API and worker"
	@echo "Run 'make check-services' to verify services"
