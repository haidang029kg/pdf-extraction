# Services Setup Guide

This guide explains how to set up and manage external services (PostgreSQL, Redis, LocalStack) required by the Freight Invoice Extractor application.

## Quick Start

Since you're managing services separately, start them manually:

```bash
# 1. Start PostgreSQL
docker run --name freight_audit_postgres \
  -e POSTGRES_USER=freight_audit \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=freight_audit \
  -p 5432:5432 \
  -d postgres:15-alpine

# 2. Start Redis
docker run --name freight_audit_redis \
  -p 6379:6379 \
  -d redis:7-alpine

# 3. Start LocalStack
docker run --name freight_audit_localstack \
  -e SERVICES=s3,textract \
  -e DEBUG=1 \
  -e DATA_DIR=/tmp/localstack/data \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -p 4566:4566 \
  -p 4510-4559:4510-4559 \
  -d localstack/localstack:latest
```

Then run:
```bash
make install-deps    # Install dependencies
make init-localstack  # Initialize LocalStack S3 bucket
make init-db          # Initialize database
make run-api          # Start FastAPI server
make run-worker       # Start Celery worker
```

## Service Details

### PostgreSQL

**Purpose**: Application database

**Default Connection**:
```
postgresql://freight_audit:your_password@localhost:5432/freight_audit
```

**Start individually**:
```bash
docker run --name freight_audit_postgres \
  -e POSTGRES_USER=freight_audit \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=freight_audit \
  -p 5432:5432 \
  -d postgres:15-alpine
```

**Check status**:
```bash
docker ps | grep postgres
```

**Stop**:
```bash
docker stop freight_audit_postgres
```

**Start again**:
```bash
docker start freight_audit_postgres
```

### Redis

**Purpose**: Task queue and caching for Celery

**Default Connection**:
```
redis://localhost:6379/0
```

**Start individually**:
```bash
docker run --name freight_audit_redis \
  -p 6379:6379 \
  -d redis:7-alpine
```

**Check status**:
```bash
docker ps | grep redis
```

**Stop**:
```bash
docker stop freight_audit_redis
```

**Start again**:
```bash
docker start freight_audit_redis
```

### LocalStack

**Purpose**: AWS services emulation (S3, Textract)

**Default Connection**:
```
AWS Endpoint: http://localhost:4566
Region: us-east-1
Access Key: test
Secret Key: test
```

**Start individually**:
```bash
docker run --name freight_audit_localstack \
  -e SERVICES=s3,textract \
  -e DEBUG=1 \
  -e DATA_DIR=/tmp/localstack/data \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -p 4566:4566 \
  -p 4510-4559:4510-4559 \
  -d localstack/localstack:latest
```

**Check status**:
```bash
docker ps | grep localstack
```

**Stop**:
```bash
docker stop freight_audit_localstack
```

**Start again**:
```bash
docker start freight_audit_localstack
```

## Environment Configuration

Update `.env` file to connect to your services:

```bash
# PostgreSQL
DATABASE_URL=postgresql://freight_audit:your_password@localhost:5432/freight_audit

# Redis
REDIS_URL=redis://localhost:6379/0

# AWS / LocalStack
AWS_ENDPOINT_URL=http://localhost:4566
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test

# S3
S3_BUCKET_NAME=freight-invoices

# LLM
GOOGLE_API_KEY=your-google-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
DEFAULT_LLM_PROVIDER=gemini_2.5

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

## Initialization

### Setup LocalStack S3 Bucket

Run this once after starting LocalStack:
```bash
uv run python scripts/setup_localstack.py
```

This creates:
- S3 bucket: `freight-invoices`
- Folders: `uploads/`, `processed/`, `review-images/`

### Initialize Database

Run this once after starting PostgreSQL:
```bash
uv run python scripts/init_db.py
```

This creates all database tables:
- jobs
- invoice_data
- ocr_coordinates
- review_annotations

## Service Management

### Start All Services (manually)

Since services are managed separately, you need to start them individually:

```bash
# Terminal 1
docker run --name freight_audit_postgres \
  -e POSTGRES_USER=freight_audit \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=freight_audit \
  -p 5432:5432 \
  -d postgres:15-alpine

# Terminal 2
docker run --name freight_audit_redis \
  -p 6379:6379 \
  -d redis:7-alpine

# Terminal 3
docker run --name freight_audit_localstack \
  -e SERVICES=s3,textract \
  -e DEBUG=1 \
  -e DATA_DIR=/tmp/localstack/data \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -p 4566:4566 \
  -p 4510-4559:4510-4559 \
  -d localstack/localstack:latest
```

### Stop All Services

```bash
docker stop freight_audit_postgres freight_audit_redis freight_audit_localstack
```

### Check Status

```bash
# PostgreSQL
docker ps | grep postgres

# Redis  
docker ps | grep redis

# LocalStack
docker ps | grep localstack

# All services
docker ps
```

### View Logs

```bash
# PostgreSQL
docker logs freight_audit_postgres

# Redis
docker logs freight_audit_redis

# LocalStack
docker logs freight_audit_localstack

# Follow logs in real-time
docker logs -f freight_audit_postgres
```

## Data Persistence

Data is persisted in Docker volumes:

| Service | Volume Name | Location |
|----------|--------------|----------|
| PostgreSQL | pdf-extract_postgres_data | /var/lib/postgresql/data |
| Redis | pdf-extract_redis_data | /data |
| LocalStack | pdf-extract_localstack_data | /tmp/localstack/data |

**Backup volumes**:
```bash
# PostgreSQL
docker run --rm -v pdf-extract_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Redis
docker run --rm -v pdf-extract_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz /data

# LocalStack
docker run --rm -v pdf-extract_localstack_data:/data -v $(pwd):/backup alpine tar czf /backup/localstack_backup.tar.gz /data
```

**Restore volumes**:
```bash
# Restore from backup
docker run --rm -v $(pwd):/backup -v pdf-extract_postgres_data:/data alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

## Testing Connections

### Test PostgreSQL

```bash
uv run python -c "
import psycopg2
conn = psycopg2.connect('postgresql://freight_audit:your_password@localhost:5432/freight_audit')
print('✅ Connected to PostgreSQL!')
"
```

### Test Redis

```bash
uv run python -c "
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
r.ping()
print('✅ Redis connected!')
"
```

### Test LocalStack

```bash
# Check health
curl http://localhost:4566/health

# List buckets
docker exec freight_audit_localstack \
  awslocal s3 ls

# Or use boto3 from within Python
uv run python scripts/setup_localstack.py
```

## Troubleshooting

### PostgreSQL Connection Issues

**Check if PostgreSQL is running**:
```bash
docker ps | grep postgres
```

**Check connection string in .env**:
```bash
DATABASE_URL=postgresql://freight_audit:your_password@localhost:5432/freight_audit
```

**Test connection**:
```bash
uv run python -c "
import psycopg2
conn = psycopg2.connect('postgresql://freight_audit:password@localhost:5432/freight_audit')
print('✅ Connected to PostgreSQL!')
"
```

### Redis Connection Issues

**Check if Redis is running**:
```bash
docker ps | grep redis
```

**Test connection**:
```bash
uv run python -c "
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
r.ping()
print('✅ Redis connected!')
"
```

### LocalStack Connection Issues

**Check if LocalStack is running**:
```bash
docker ps | grep localstack
```

**Check health endpoint**:
```bash
curl http://localhost:4566/health
```

**View LocalStack logs**:
```bash
docker logs freight_audit_localstack -f
```

**Reinitialize LocalStack**:
```bash
# Stop LocalStack
docker stop freight_audit_localstack

# Remove container
docker rm freight_audit_localstack

# Start fresh
docker run --name freight_audit_localstack \
  -e SERVICES=s3,textract \
  -e DEBUG=1 \
  -e DATA_DIR=/tmp/localstack/data \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -p 4566:4566 \
  -p 4510-4559:4510-4559 \
  -d localstack/localstack:latest

# Reinitialize S3
uv run python scripts/setup_localstack.py
```

### Service Already Running

If you get "port already in use" errors:

**Find process using port**:
```bash
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :4566  # LocalStack
```

**Kill process**:
```bash
kill -9 <PID>
```

Or stop/stop and remove existing container:
```bash
docker stop freight_audit_postgres
docker rm freight_audit_postgres
```

## Clean Up

**Stop and remove all services**:
```bash
docker stop freight_audit_postgres freight_audit_redis freight_audit_localstack
docker rm freight_audit_postgres freight_audit_redis freight_audit_localstack
```

**Remove volumes** (⚠️ deletes all data):
```bash
docker volume rm pdf-extract_postgres_data pdf-extract_redis_data pdf-extract_localstack_data
```

## Production Deployment

For production, replace LocalStack with real AWS services:

1. **Update AWS credentials** in `.env`:
```bash
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=your_aws_region
AWS_ENDPOINT_URL=https://<region>.amazonaws.com
```

2. **Use managed services**:
   - AWS RDS for PostgreSQL
   - AWS ElastiCache for Redis
   - AWS S3 and Textract (real services)

3. **No code changes needed** - application works the same!
