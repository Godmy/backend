#!/bin/bash
# Celery worker startup script with graceful shutdown handling

set -e

echo "Starting Celery worker..."

# Trap SIGTERM and SIGINT for graceful shutdown
trap 'echo "Received shutdown signal, stopping worker gracefully..."; kill -TERM $PID' SIGTERM SIGINT

# Get configuration from environment
CONCURRENCY=${CELERY_WORKER_CONCURRENCY:-4}
MAX_TASKS_PER_CHILD=${CELERY_WORKER_MAX_TASKS_PER_CHILD:-1000}
LOG_LEVEL=${LOG_LEVEL:-info}

# Start Celery worker in background
celery -A workers.celery_worker worker \
    --loglevel=$LOG_LEVEL \
    --concurrency=$CONCURRENCY \
    --max-tasks-per-child=$MAX_TASKS_PER_CHILD \
    --time-limit=600 \
    --soft-time-limit=540 &

# Get the PID of the background process
PID=$!

echo "Celery worker started with PID: $PID"

# Wait for the background process
wait $PID

echo "Celery worker stopped"
