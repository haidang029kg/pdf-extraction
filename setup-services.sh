#!/bin/bash

set -e

echo "=========================================="
echo "Freight Invoice Extractor - Setup Services"
echo "=========================================="
echo ""

echo "Step 1: Checking prerequisites..."
command -v uv >/dev/null 2>&1 || { echo "❌ uv not found. Install with: curl -LsSf https://astral.sh/uv | sh"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Install Docker first"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose not found. Install Docker Compose first"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3.11+ not found"; exit 1; }
echo "✅ Prerequisites check passed"
echo ""

echo "Step 2: Installing Python dependencies..."
uv sync
echo "✅ Dependencies installed"
echo ""

echo "Step 3: Starting external services (PostgreSQL, Redis, LocalStack)..."
echo "This will start services in background containers..."
docker-compose -f docker-compose.services.yml up -d
echo "⏳ Waiting for services to be ready..."
sleep 5
echo "✅ External services started"
echo ""

echo "Step 4: Setting up LocalStack S3 bucket..."
uv run python scripts/setup_localstack.py
echo ""

echo "Step 5: Initializing database..."
uv run python scripts/init_db.py
echo ""

echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "External Services Status:"
docker-compose -f docker-compose.services.yml ps
echo ""
echo "To start the application:"
echo ""
echo "Terminal 1 - FastAPI Server:"
echo "  uv run uvicorn app.main:app --reload"
echo ""
echo "Terminal 2 - Celery Worker:"
echo "  uv run celery -A app.workers.celery_app worker --loglevel=info"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "To stop services:"
echo "  docker-compose -f docker-compose.services.yml down"
echo ""
