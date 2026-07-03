#!/bin/sh
set -e

echo "Running migrations..."
uv run alembic upgrade head

echo "Starting API..."
exec uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
