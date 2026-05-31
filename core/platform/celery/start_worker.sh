#!/bin/bash

set -e

echo "Starting Celery worker..."

trap 'echo "Received shutdown signal, stopping worker gracefully..."; kill -TERM $PID' SIGTERM SIGINT

CONCURRENCY=${CELERY_WORKER_CONCURRENCY:-4}
MAX_TASKS_PER_CHILD=${CELERY_WORKER_MAX_TASKS_PER_CHILD:-1000}
LOG_LEVEL=${LOG_LEVEL:-info}

celery -A core.platform.celery.worker worker \
    --loglevel=$LOG_LEVEL \
    --concurrency=$CONCURRENCY \
    --max-tasks-per-child=$MAX_TASKS_PER_CHILD \
    --time-limit=600 \
    --soft-time-limit=540 &

PID=$!

echo "Celery worker started with PID: $PID"
wait $PID
echo "Celery worker stopped"
