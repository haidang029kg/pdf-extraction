# Freight Invoice Extractor

A FastAPI-based system for extracting structured data from freight invoice PDFs using OCR and LLM technologies.

## Features

- PDF upload via REST API
- OCR text extraction with coordinate tracking
- LLM-powered intelligent data extraction
- Human review workflow with highlighted annotations
- JSON and Excel export
- Async processing with Celery

## Tech Stack

- **FastAPI**: Web framework
- **PostgreSQL**: Database (external service)
- **Redis**: Queue and cache (external service)
- **LocalStack**: AWS services emulation - S3, Textract (external service)
- **Celery**: Background task processing
- **Boto3**: AWS SDK

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Freight Invoice Extractor App          │
│              (FastAPI + Celery)                   │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │FastAPI   │  │Celery    │  │Celery    │  │
│  │Server     │  │Worker     │  │Beat       │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────┘
         │                │                │
         │                │                │
         ▼                ▼                ▼
┌──────────────┐  ┌──────────┐  ┌─────────────┐
│ PostgreSQL   │  │  Redis   │  │ LocalStack   │
│  (External)  │  │ (External)  │  / AWS      │
│             │  │          │  │              │
│ Port: 5432 │  │ Port: 6379 │  │ Port: 4566  │
└──────────────┘  └──────────┘  └─────────────┘
```

## Getting Started

### Prerequisites

- Python 3.11+
- uv (fast Python package installer)
- Docker & Docker Compose

Install uv if not already installed:
```bash
pip install uv
```

### Quick Start (Recommended)

```bash
make setup-dev
```

This will:
- Install Python dependencies
- Start external services (PostgreSQL, Redis, LocalStack)
- Initialize LocalStack S3 bucket
- Create database tables

Then start the application:
```bash
make dev
```

### External Services Setup

You need to run the following services separately via Docker:

#### 1. PostgreSQL
```bash
docker run --name freight_audit_postgres \
  -e POSTGRES_USER=freight_audit \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=freight_audit \
  -p 5432:5432 \
  -d postgres:15-alpine
```

#### 2. Redis
```bash
docker run --name freight_audit_redis \
  -p 6379:6379 \
  -d redis:7-alpine
```

#### 3. LocalStack
```bash
docker run --name freight_audit_localstack \
  -e SERVICES=s3,textract \
  -e DEBUG=1 \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -p 4566:4566 \
  -p 4510-4559:4510-4559 \
  -d localstack/localstack:latest
```

Or use Docker Compose for services (separate from app):

### Using Makefile

All common commands are available via Makefile:

```bash
make help              # Show all available commands
make install           # Install and initialize everything
make install-deps       # Install dependencies
make start-services      # Start PostgreSQL, Redis, LocalStack
make stop-services       # Stop all services
make init-localstack    # Initialize LocalStack S3 bucket
make init-db            # Initialize database tables
make run-api            # Start FastAPI server
make run-worker         # Start Celery worker
make dev                # Start API and worker together
make test               # Run all tests
make lint               # Run linter
make format             # Format code
make clean              # Clean cache files
make check-services      # Check if all services are running
```

See all available commands:
```bash
make help
```

### Docker Compose for Services (separate from app):
```yaml
# docker-compose.services.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: freight_audit_postgres
    environment:
      - POSTGRES_USER=freight_audit
      - POSTGRES_PASSWORD=your_password
      - POSTGRES_DB=freight_audit
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    container_name: freight_audit_redis
    ports:
      - "6379:6379"

  localstack:
    image: localstack/localstack:latest
    container_name: freight_audit_localstack
    environment:
      - SERVICES=s3,textract
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
      - AWS_DEFAULT_REGION=us-east-1
    ports:
      - "4566:4566"
      - "4510-4559:4510-4559"
```

Run services:
```bash
docker-compose -f docker-compose.services.yml up -d
```

### Application Setup

1. Clone repository
```bash
git clone <repository-url>
cd pdf-extract
```

2. Create environment file
```bash
cp .env.example .env
```

3. Update `.env` with your configuration
```bash
# Update service connection strings if needed
DATABASE_URL=postgresql://freight_audit:your_actual_password@localhost:5432/freight_audit
REDIS_URL=redis://localhost:6379/0
AWS_ENDPOINT_URL=http://localhost:4566

# Add your API keys
GOOGLE_API_KEY=your-actual-google-api-key
ANTHROPIC_API_KEY=your-actual-anthropic-api-key
```

4. Install dependencies with uv
```bash
uv sync
```

5. Initialize LocalStack S3 bucket (run once)
```bash
uv run python scripts/setup_localstack.py
```

6. Initialize database (run once)
```bash
uv run python scripts/init_db.py
```

7. Start FastAPI server
```bash
uv run uvicorn app.main:app --reload
```

8. In another terminal, start Celery worker
```bash
uv run celery -A app.workers.celery_app worker --loglevel=info
```

Optional: Start Celery beat (for scheduled tasks)
```bash
uv run celery -A app.workers.celery_app beat --loglevel=info
```

## API Endpoints

### Upload PDF
```bash
POST /api/v1/upload
Content-Type: multipart/form-data

curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@invoice.pdf" \
  -F "ocr_provider=textract" \
  -F "llm_provider=gemini_2.5"
```

### Check Status
```bash
GET /api/v1/jobs/{job_id}/status

curl http://localhost:8000/api/v1/jobs/{job_id}/status
```

### Get Data
```bash
GET /api/v1/jobs/{job_id}/data

curl http://localhost:8000/api/v1/jobs/{job_id}/data
```

### Download JSON
```bash
GET /api/v1/jobs/{job_id}/download/json

curl http://localhost:8000/api/v1/jobs/{job_id}/download/json \
  -o output.json
```

### Download Excel
```bash
GET /api/v1/jobs/{job_id}/download/excel

curl http://localhost:8000/api/v1/jobs/{job_id}/download/excel \
  -o output.xlsx
```

## Development

### Running Tests
```bash
uv run pytest
```

### Adding Dependencies
```bash
uv add <package-name>
```

### Removing Dependencies
```bash
uv remove <package-name>
```

### Database Migrations
```bash
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

## Project Structure

```
pdf-extract/
├── app/
│   ├── api/           # API routes
│   ├── models/         # Pydantic schemas and SQLAlchemy models
│   ├── services/       # OCR and LLM services
│   ├── workers/        # Celery background tasks
│   ├── db/            # Database session management
│   └── utils/         # S3 service
├── scripts/           # Setup and utility scripts
├── tests/            # Test suite
├── pyproject.toml     # Project configuration
└── .env              # Environment variables
```

## Environment Variables

| Variable | Description | Default |
|-----------|-------------|-----------|
| APP_NAME | Application name | Freight Invoice Extractor |
| APP_VERSION | Application version | 1.0.0 |
| DEBUG | Debug mode | True |
| DATABASE_URL | PostgreSQL connection string | postgresql://... |
| REDIS_URL | Redis connection string | redis://localhost:6379/0 |
| AWS_ENDPOINT_URL | AWS/LocalStack endpoint | http://localhost:4566 |
| AWS_REGION | AWS region | us-east-1 |
| AWS_ACCESS_KEY_ID | AWS access key | test |
| AWS_SECRET_ACCESS_KEY | AWS secret key | test |
| S3_BUCKET_NAME | S3 bucket name | freight-invoices |
| GOOGLE_API_KEY | Google AI API key | (required) |
| ANTHROPIC_API_KEY | Anthropic API key | (required) |
| DEFAULT_LLM_PROVIDER | Default LLM provider | gemini_2.5 |
| CELERY_BROKER_URL | Celery broker URL | redis://localhost:6379/1 |
| CELERY_RESULT_BACKEND | Celery result backend | redis://localhost:6379/2 |
| MAX_FILE_SIZE_MB | Max file upload size | 50 |

## Services Management

### Check Service Status
```bash
# PostgreSQL
docker ps | grep postgres

# Redis
docker ps | grep redis

# LocalStack
docker ps | grep localstack
```

### View Service Logs
```bash
# PostgreSQL
docker logs freight_audit_postgres

# Redis
docker logs freight_audit_redis

# LocalStack
docker logs freight_audit_localstack
```

### Stop Services
```bash
docker stop freight_audit_postgres freight_audit_redis freight_audit_localstack
```

### Start Services
```bash
docker start freight_audit_postgres freight_audit_redis freight_audit_localstack
```

### Remove Services
```bash
docker stop freight_audit_postgres freight_audit_redis freight_audit_localstack
docker rm freight_audit_postgres freight_audit_redis freight_audit_localstack
```

## Docker Deployment

### Using Makefile

Build and run the application container:

```bash
# Build image
make docker-build

# Run application
make docker-run

# Stop application
make docker-stop
```

### Manual Docker Commands

Build and run the application container:

```bash
# Build image
docker build -t freight-invoice-extractor .

# Run container
docker run --name freight_extractor_app \
  -p 8000:8000 \
  --env-file .env \
  --link freight_audit_postgres:postgres \
  --link freight_audit_redis:redis \
  --link freight_audit_localstack:localstack \
  freight-invoice-extractor
```

## Troubleshooting

### PostgreSQL Connection Failed
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Test connection
uv run python -c "import psycopg2; conn = psycopg2.connect('postgresql://freight_audit:password@localhost:5432/freight_audit'); print('Connected!')"
```

### Redis Connection Failed
```bash
# Check if Redis is running
docker ps | grep redis

# Test connection
uv run python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping(); print('Connected!')"
```

### LocalStack Connection Failed
```bash
# Check if LocalStack is running
docker ps | grep localstack

# Check LocalStack health
curl http://localhost:4566/health

# View LocalStack logs
docker logs freight_audit_localstack
```

### Dependencies Not Found
```bash
# Reinstall dependencies
uv sync

# Clear cache and reinstall
rm -rf .venv uv.lock
uv sync
```

## License

MIT
