# External Services Setup Guide

This guide explains how to set up and manage the external services (PostgreSQL, Redis, LocalStack) required by the Freight Invoice Extractor application.

## Quick Start

Run all services with one command:
```bash
./setup-services.sh
```

This will:
1. Install Python dependencies
2. Start PostgreSQL, Redis, and LocalStack containers
3. Initialize LocalStack S3 bucket
4. Create database tables

Then start the application:
```bash
# Terminal 1
uv run uvicorn app.main:app --reload

# Terminal 2
uv run celery -A app.workers.celery_app worker --loglevel=info
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

**View logs**:
```bash
docker logs freight_audit_postgres
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

**View logs**:
```bash
docker logs freight_audit_redis
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
curl http://localhost:4566/health
```

**View logs**:
```bash
docker logs freight_audit_localstack
```

## Docker Compose (Services Only)

Use the separate services-only compose file:
```bash
docker-compose -f docker-compose.services.yml up -d
```

## Service Management

### Start All Services
```bash
docker-compose -f docker-compose.services.yml up -d
```

### Stop All Services
```bash
docker-compose -f docker-compose.services.yml down
```

### Restart All Services
```bash
docker-compose -f docker-compose.services.yml restart
```

### View All Services Status
```bash
docker-compose -f docker-compose.services.yml ps
```

### View All Services Logs
```bash
docker-compose -f docker-compose.services.yml logs -f
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

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

## Initialization Scripts

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

## Troubleshooting

### PostgreSQL Connection Issues

**Check if PostgreSQL is running**:
```bash
docker ps | grep postgres
```

**Check connection string in .env**:
```bash
DATABASE_URL=postgresql://freight_audit:password@localhost:5432/freight_audit
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
print('✅ Connected to Redis!')
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

**Find process using the port**:
```bash
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :4566  # LocalStack
```

**Kill the process**:
```bash
kill -9 <PID>
```

Or stop the existing container:
```bash
docker stop freight_audit_postgres
docker stop freight_audit_redis
docker stop freight_audit_localstack
```

## Data Persistence

Data is persisted in Docker volumes:

| Service | Volume Name | Location |
|----------|--------------|----------|
| PostgreSQL | postgres_data | /var/lib/postgresql/data |
| Redis | redis_data | /data |
| LocalStack | localstack_data | /tmp/localstack/data |

**Backup volumes**:
```bash
# PostgreSQL
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Redis
docker run --rm -v redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz /data

# LocalStack
docker run --rm -v localstack_data:/data -v $(pwd):/backup alpine tar czf /backup/localstack_backup.tar.gz /data
```

**Restore volumes**:
```bash
# Restore from backup
docker run --rm -v $(pwd):/backup -v postgres_data:/data alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

## Clean Up

**Stop and remove all services**:
```bash
docker-compose -f docker-compose.services.yml down
```

**Remove volumes** (⚠️ deletes all data):
```bash
docker-compose -f docker-compose.services.yml down -v
```

**Clean up unused resources**:
```bash
docker system prune -a
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
