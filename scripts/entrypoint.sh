#!/bin/sh
set -e

echo "Running migrations..."
.venv/bin/alembic upgrade head

echo "Starting API..."
exec .venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
