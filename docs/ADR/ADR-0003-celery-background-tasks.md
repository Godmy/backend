# Celery Background Task Processing

**Status**: ✅ Active
**Version**: 1.0
**Dependencies**: Redis, Celery 5.3+, Flower

## Overview

Celery integration provides asynchronous background task processing for long-running operations without blocking HTTP requests. This includes email sending, thumbnail generation, file cleanup, and scheduled periodic tasks.

## Features

### Core Capabilities

1. **Asynchronous Task Execution**
   - Email sending (verification, password reset, welcome)
   - Thumbnail generation for uploaded images
   - File cleanup and maintenance
   - Custom task implementations

2. **Retry Logic**
   - Exponential backoff starting at 1 minute
   - Maximum 5 retries for email tasks
   - Maximum 3 retries for file tasks
   - Jitter to prevent thundering herd

3. **Dead Letter Queue**
   - Automatic routing of failed tasks after max retries
   - Separate queue for inspection and reprocessing
   - Task failure tracking and logging

4. **Periodic Tasks (Celery Beat)**
   - Daily file cleanup at 2 AM
   - Hourly health checks
   - Configurable cron-like scheduling

5. **Monitoring & Observability**
   - Flower web UI (port 5555)
   - Health check integration
   - Structured logging with request ID correlation
   - Task execution metrics

6. **Graceful Shutdown**
   - SIGTERM handling
   - Task completion before worker shutdown
   - No task loss during deployment

## Architecture

```
HTTP Request → API Handler → Celery Task (Async)
                ↓
         Task Queue (Redis)
                ↓
         Celery Worker → Task Execution
                ↓
         Result Backend (Redis)
```

### Components

- **Celery App** (`core/celery_app.py`): Main Celery instance and configuration
- **Tasks** (`tasks/`): Task implementations organized by type
- **Workers** (`workers/celery_worker.py`): Worker entry point
- **Middleware** (`core/middleware/celery_context.py`): Request context propagation

## Configuration

### Environment Variables

```bash
# Redis Configuration (shared with main app)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Celery Worker Settings
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000

# File Cleanup Settings
FILE_CLEANUP_MAX_AGE_DAYS=90
TEMP_DIR=temp
```

### Queue Configuration

Three priority queues are configured:

1. **default**: Standard tasks (email, thumbnails)
2. **high_priority**: Urgent tasks
3. **low_priority**: Cleanup and maintenance
4. **dead_letter**: Failed tasks after max retries

## Usage

### Starting Services

#### Development (Docker Compose)

```bash
# Start all services including Celery worker and beat
docker-compose -f docker-compose.dev.yml up

# Services started:
# - app: Main application (port 8000)
# - celery_worker: Task worker
# - celery_beat: Periodic task scheduler
# - flower: Monitoring UI (port 5555)
```

#### Production

```bash
# Start production services
docker-compose up -d

# Check worker status
docker-compose logs celery_worker
docker-compose logs celery_beat
```

#### Manual Worker Start

```bash
# Start worker
celery -A workers.celery_worker worker --loglevel=info --concurrency=4

# Start beat scheduler
celery -A workers.celery_worker beat --loglevel=info

# Start Flower monitoring
celery -A workers.celery_worker flower --port=5555
```

### Calling Tasks from Code

#### Email Tasks

```python
from tasks.email_tasks import send_verification_email_task
from core.middleware import get_celery_context

# In a GraphQL resolver or API endpoint
def send_verification(request, user_email, username, token):
    # Get request context for tracing
    context = get_celery_context(request)

    # Queue the task (returns immediately)
    task = send_verification_email_task.delay(
        to_email=user_email,
        username=username,
        token=token,
        request_id=context.get("request_id"),
    )

    # Task is now running in background
    return {"task_id": task.id, "status": "queued"}
```

#### File Processing Tasks

```python
from tasks.file_tasks import generate_thumbnail_task

def handle_file_upload(file_path, stored_filename):
    # Queue thumbnail generation
    task = generate_thumbnail_task.delay(
        file_path=file_path,
        stored_filename=stored_filename,
    )

    # Continue without waiting
    return {"file_uploaded": True, "thumbnail_task_id": task.id}
```

#### Checking Task Status

```python
from core.celery_app import celery_app

def get_task_status(task_id):
    result = celery_app.AsyncResult(task_id)

    return {
        "task_id": task_id,
        "state": result.state,  # PENDING, STARTED, SUCCESS, FAILURE, RETRY
        "info": result.info,
        "ready": result.ready(),
        "successful": result.successful(),
    }
```

### Available Tasks

#### Email Tasks

- `tasks.send_email`: Generic email sending
- `tasks.send_verification_email`: Email verification
- `tasks.send_password_reset_email`: Password reset
- `tasks.send_welcome_email`: Welcome message

#### File Tasks

- `tasks.generate_thumbnail`: Image thumbnail generation
- `tasks.cleanup_old_files`: Delete old files from directory
- `tasks.cleanup_temporary_files`: Clean temp directories

#### Periodic Tasks

- `tasks.periodic_file_cleanup`: Daily cleanup (2 AM)
- `tasks.periodic_health_check`: Hourly health check

## Monitoring

### Flower Web UI

Access Flower at `http://localhost:5555`

**Features:**
- Real-time task monitoring
- Worker status and statistics
- Task history and results
- Task rate graphs
- Worker pool management

### Health Check

Celery status is included in the detailed health endpoint:

```bash
curl http://localhost:8000/health/detailed
```

Response includes:
```json
{
  "status": "healthy",
  "components": {
    "celery": {
      "status": "healthy",
      "workers_count": 1,
      "active_tasks": 0,
      "workers": ["celery@hostname"]
    }
  }
}
```

### Logs

All tasks emit structured logs with request ID correlation:

```json
{
  "timestamp": "2025-10-27T06:00:00Z",
  "level": "INFO",
  "message": "Task started: tasks.send_email",
  "task_id": "abc-123",
  "task_name": "tasks.send_email",
  "request_id": "req-456"
}
```

## Retry and Error Handling

### Automatic Retry

Tasks automatically retry on failure with exponential backoff:

```python
# Configuration (EmailTask base class)
autoretry_for = (Exception,)
retry_kwargs = {"max_retries": 5}
retry_backoff = True  # Exponential backoff
retry_backoff_max = 600  # Max 10 minutes
retry_jitter = True  # Add randomness
```

**Retry Schedule:**
1. Immediate failure
2. ~1 minute later
3. ~2 minutes later
4. ~4 minutes later
5. ~8 minutes later
6. After 5 retries → Dead Letter Queue

### Dead Letter Queue

Failed tasks move to the `dead_letter` queue:

```bash
# Inspect dead letter queue
celery -A workers.celery_worker inspect active_queues

# Purge dead letter queue
celery -A workers.celery_worker purge -Q dead_letter
```

### Manual Retry

```python
from core.celery_app import celery_app

# Retry a specific task
task = celery_app.AsyncResult(task_id)
task.retry()
```

## Performance Tuning

### Worker Concurrency

```bash
# Set via environment variable
CELERY_WORKER_CONCURRENCY=8

# Or via command line
celery -A workers.celery_worker worker --concurrency=8
```

**Recommended values:**
- Development: 2-4 workers
- Production: Number of CPU cores

### Task Time Limits

Tasks have hard and soft time limits:
- Soft limit: 540 seconds (9 minutes)
- Hard limit: 600 seconds (10 minutes)

### Worker Recycling

Workers restart after processing 1000 tasks to prevent memory leaks:

```bash
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000
```

## Security Considerations

1. **Task Serialization**: JSON only (no pickle)
2. **Input Validation**: All task parameters validated
3. **Authentication**: Tasks inherit security context
4. **Sensitive Data**: Not stored in task queue

## Troubleshooting

### Workers Not Starting

```bash
# Check Redis connection
redis-cli ping

# Check worker logs
docker-compose logs celery_worker

# Start worker manually for debugging
celery -A workers.celery_worker worker --loglevel=debug
```

### Tasks Not Executing

```bash
# Check if workers are receiving tasks
celery -A workers.celery_worker inspect active

# Check registered tasks
celery -A workers.celery_worker inspect registered

# Monitor task queue
redis-cli LLEN celery
```

### High Memory Usage

```bash
# Reduce concurrency
CELERY_WORKER_CONCURRENCY=2

# Reduce max tasks per child
CELERY_WORKER_MAX_TASKS_PER_CHILD=500

# Restart workers regularly
docker-compose restart celery_worker
```

### Dead Letter Queue Filling Up

```bash
# Inspect failed tasks
celery -A workers.celery_worker events

# Check logs for specific errors
grep "Task failed" logs/*.log

# Purge after fixing issues
celery -A workers.celery_worker purge -Q dead_letter
```

## Testing

### Unit Tests

```bash
# Run Celery tests
pytest tests/test_celery_tasks.py -v

# Test with coverage
pytest tests/test_celery_tasks.py --cov=tasks --cov=core.celery_app
```

### Integration Tests

```bash
# Start test environment
docker-compose -f docker-compose.dev.yml up -d

# Run integration tests
pytest tests/test_celery_tasks.py -m integration

# Check task execution
celery -A workers.celery_worker inspect stats
```

### Manual Testing

```python
# In Python shell
from tasks.email_tasks import send_email_task

# Queue test task
task = send_email_task.delay(
    to_email="test@example.com",
    subject="Test",
    html_content="<p>Test</p>"
)

# Check status
print(task.state)  # PENDING, STARTED, SUCCESS, etc.
print(task.result)  # Task return value
```

## Migration Guide

### Updating Existing Email Calls

**Before (synchronous):**
```python
from core.email_service import email_service

email_service.send_verification_email(email, username, token)
```

**After (asynchronous):**
```python
from tasks.email_tasks import send_verification_email_task

send_verification_email_task.delay(email, username, token)
```

### Updating File Processing

**Before:**
```python
file_storage_service.create_thumbnail(content, filename)
```

**After:**
```python
from tasks.file_tasks import generate_thumbnail_task

generate_thumbnail_task.delay(file_path, filename)
```

## Best Practices

1. **Task Idempotency**: Design tasks to be safely retried
2. **Short-Lived Tasks**: Keep tasks under 5 minutes
3. **Async All the Way**: Don't block on task results
4. **Request Tracing**: Always pass request_id
5. **Error Handling**: Let retry logic handle transient failures
6. **Monitoring**: Check Flower regularly
7. **Resource Limits**: Set appropriate time/memory limits

## Related Documentation

- [Email Service](email_service.md)
- [File Upload System](file_upload.md)
- [Redis Caching](redis_caching.md)
- [Structured Logging](structured_logging.md)
- [Graceful Shutdown](graceful_shutdown.md)

## References

- [Celery Documentation](https://docs.celeryq.dev/)
- [Flower Documentation](https://flower.readthedocs.io/)
- [Redis Documentation](https://redis.io/docs/)
