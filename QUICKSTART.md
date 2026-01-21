# Quick Start Guide

## Fast Setup

### 1. Start Services (manually, in 3 separate terminals)

```bash
# Terminal 1 - PostgreSQL
docker run --name freight_audit_postgres \
  -e POSTGRES_USER=freight_audit \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=freight_audit \
  -p 5432:5432 \
  -d postgres:15-alpine

# Terminal 2 - Redis
docker run --name freight_audit_redis \
  -p 6379:6379 \
  -d redis:7-alpine

# Terminal 3 - LocalStack
docker run --name freight_audit_localstack \
  -e SERVICES=s3,textract \
  -e DEBUG=1 \
  -e DATA_DIR=/tmp/localstack/data \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -p 4566:4566 \
  -p 4510-4559:4510-4559 \
  -d localstack/localstack:latest
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Update API Keys

Edit `.env` and add your actual keys:
```bash
GOOGLE_API_KEY=your-actual-google-api-key
ANTHROPIC_API_KEY=your-actual-anthropic-api-key
```

### 4. Initialize Services

```bash
uv run python scripts/setup_localstack.py
```

This initializes the S3 bucket for file uploads.

### 5. Initialize Database

```bash
uv run python scripts/init_db.py
```

This creates the database tables.

### 6. Start Application

```bash
# Terminal 1 - FastAPI server
uv run uvicorn app.main:app --reload

# Terminal 2 - Celery worker
uv run celery -A app.workers.celery_app worker --loglevel=info
```

## Verify Services Running

```bash
# Check PostgreSQL
docker ps | grep freight_audit_postgres

# Check Redis
docker ps | grep freight_audit_redis

# Check LocalStack
docker ps | grep freight_audit_localstack
```

## Check Connections

```bash
# Check PostgreSQL
uv run python -c "import psycopg2; conn = psycopg2.connect('postgresql://freight_audit:your_password@localhost:5432/freight_audit'); print('✅ PostgreSQL connected')"

# Check Redis
uv run python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping() and print('✅ Redis connected')"

# Check LocalStack
curl http://localhost:4566/health
```

## API Available

Once services are running:

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Upload PDF**: `POST /api/v1/upload`
- **Check Status**: `GET /api/v1/jobs/{job_id}/status`
- **Get Data**: `GET /api/v1/jobs/{job_id}/data`
- **Download JSON**: `GET /api/v1/jobs/{job_id}/download/json`

## Available Makefile Commands

```bash
make help              # Show all commands
make install-deps       # Install dependencies
make init-localstack    # Initialize LocalStack S3 bucket
make init-db            # Initialize database
make run-api            # Start FastAPI server
make run-worker         # Start Celery worker
make dev                # Start API and worker
make test               # Run tests
make lint               # Check code quality
make format             # Format code
make clean              # Clean cache
make check-services      # Check if services are running
```

## Common Issues

### Port Already in Use

```bash
# Find process using port
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :4566  # LocalStack

# Kill process
kill -9 <PID>

# Or stop existing container
docker stop freight_audit_postgres
docker rm freight_audit_postgres
```

### Connection Failed

```bash
# Update .env with correct connection string
DATABASE_URL=postgresql://freight_audit:your_password@localhost:5432/freight_audit
REDIS_URL=redis://localhost:6379/0
AWS_ENDPOINT_URL=http://localhost:4566
```

### Service Not Responding

```bash
# Check service status
docker ps | grep -E "postgres|redis|localstack"

# Check health
curl http://localhost:4566/health
curl http://localhost:8000/health

# View logs
docker logs freight_audit_localstack
docker logs freight_audit_postgres
docker logs freight_audit_redis
```

## Full Documentation

- **README.md** - Complete project documentation
- **SERVICES_SETUP.md** - Detailed services management guide
- **PHASE1_STATUS.md** - Phase 1 status
- **PHASE2_OCR_IMPLEMENTATION.md** - Phase 2 (OCR)
- **PHASE3_LLM_INTEGRATION.md** - Phase 3 (LLM)
- **PHASE4_COORDINATE_MAPPING.md** - Phase 4 (Review)
- **PHASE5_EXPORT_VALIDATION.md** - Phase 5 (Export)
- **PHASE6_TESTING_DEPLOYMENT.md** - Phase 6 (Testing)
- **PHASE7_PRODUCTION_SCALING.md** - Phase 7 (Production)

## Next Steps

1. Update API keys in `.env`
2. Start services manually (see above)
3. Run `make install-deps`
4. Initialize LocalStack and database
5. Start FastAPI and Celery worker
6. Open http://localhost:8000/docs
7. Upload a test PDF and verify the workflow
