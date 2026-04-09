#!/bin/bash
set -e

# Run celery worker
echo "Starting Celery worker..."
exec uv run celery --app=worker.celery worker --loglevel=INFO
