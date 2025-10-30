# Request ID & Distributed Tracing

Comprehensive request tracking system for tracing requests across the application, including HTTP handlers, GraphQL resolvers, database queries, and background tasks.

## Features

- Automatic request ID generation (UUID) for every HTTP request
- Request ID propagation through all application layers
- Context variables for thread-safe request tracking
- X-Request-ID header in all responses
- Automatic logging with request_id and user_id
- Support for background tasks and Celery
- Tracing helpers for manual instrumentation
- GraphQL context integration

## How It Works

1. **RequestLoggingMiddleware** generates unique request_id for each request
2. Request ID stored in **context variables** (thread-safe)
3. All logs automatically include request_id and user_id
4. GraphQL context includes request_id for resolvers
5. Background tasks can propagate request_id

## Automatic Logging Format

```
[abc12345] [user:42] INFO - app - Processing request
[abc12345] [user:42] INFO - auth.services - User authenticated
[abc12345] [user:42] INFO - core.database - Query executed
```

## GraphQL Integration

```python
# In any GraphQL resolver
@strawberry.field
def my_query(self, info) -> str:
    request_id = info.context["request_id"]
    logger.info(f"Processing query")  # Automatically includes request_id
    return "result"
```

## Manual Request ID Access

```python
from core.context import get_request_id, get_user_id

def my_function():
    request_id = get_request_id()  # Current request ID
    user_id = get_user_id()  # Current user ID (if authenticated)

    logger.info("Processing")  # Automatically includes both IDs
```

## Background Tasks (Async)

```python
from core.tracing import with_request_context

@with_request_context
async def send_email_task(to_email: str):
    # request_id is automatically available in logs
    logger.info(f"Sending email to {to_email}")
```

## Celery Tasks

```python
from celery import shared_task
from core.tracing import celery_task_with_context
from core.context import get_request_id, get_user_id

@shared_task
@celery_task_with_context()
def process_report(report_id: int, request_id: str = None, user_id: int = None):
    # request_id is now set in context
    logger.info(f"Processing report {report_id}")

# Call from request handler
request_id = get_request_id()
user_id = get_user_id()
process_report.delay(
    report_id=123,
    request_id=request_id,
    user_id=user_id
)
```

## Manual Tracing Spans

```python
from core.tracing import TracingHelper

def process_order(order_id: int):
    with TracingHelper.span("process_order") as span:
        span.set_tag("order_id", order_id)

        validate_order(order_id)
        span.log("Order validated")

        charge_payment(order_id)
        span.log("Payment charged")

        fulfill_order(order_id)
        span.log("Order fulfilled")
```

## Client Usage

All HTTP responses include `X-Request-ID` header for client-side tracking:

```bash
curl -v http://localhost:8000/health
# < X-Request-ID: abc12345
```

Clients can also send their own request ID:

```bash
curl -H "X-Request-ID: custom-id-123" http://localhost:8000/health
```

## Implementation

- `core/context.py` - Context variables and logging filter
- `core/tracing.py` - Tracing decorators and helpers
- `core/middleware/request_logging.py` - Middleware with request_id generation
- `app.py` - Logging configuration with RequestContextFilter
- `tests/test_request_tracing.py` - Comprehensive test suite

## Benefits

- **Debuggability** - Trace a single request through all logs
- **Observability** - Correlate errors across services
- **Performance** - Identify slow operations in request lifecycle
- **Security** - Audit user actions with request correlation
- **Production-ready** - Thread-safe, async-compatible, zero configuration

## Usage Patterns

### Error Correlation

When debugging an error, search logs by request_id to see the entire request flow:

```bash
grep "abc12345" application.log
```

### Performance Analysis

Track request duration from start to finish:

```python
from core.context import get_request_id
import time

start_time = time.time()
# ... process request ...
duration = time.time() - start_time
logger.info(f"Request completed in {duration:.2f}s", extra={"request_id": get_request_id()})
```

### User Activity Tracking

Correlate all actions by a specific user:

```bash
grep "user:42" application.log | grep "abc12345"
```

## Integration with Other Systems

### Sentry

Request IDs are automatically included in Sentry error reports:

```python
from core.sentry import capture_exception
from core.context import get_request_id

try:
    process_something()
except Exception as e:
    capture_exception(e, extra={"request_id": get_request_id()})
```

### Prometheus

Track request duration by endpoint:

```python
from core.metrics import http_request_duration_seconds
from core.context import get_request_id
import time

start_time = time.time()
# ... process request ...
duration = time.time() - start_time
http_request_duration_seconds.labels(
    method="POST",
    endpoint="/graphql",
    status=200
).observe(duration)
```

### External APIs

Propagate request ID to external services:

```python
import httpx
from core.context import get_request_id

async def call_external_api():
    request_id = get_request_id()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/endpoint",
            headers={"X-Request-ID": request_id}
        )
    return response
```

## Best Practices

1. **Always propagate request_id** - Pass it to background tasks and external APIs
2. **Log important milestones** - Add log statements at key points in request processing
3. **Use meaningful log messages** - Make logs searchable and understandable
4. **Include context** - Add relevant metadata to log statements
5. **Monitor request duration** - Track slow requests and optimize
6. **Correlate with user actions** - Use user_id alongside request_id
7. **Clean up old logs** - Implement log retention policies

## Troubleshooting

### Request ID not appearing in logs
- Verify RequestContextFilter is added to logging configuration
- Check middleware is properly initialized
- Ensure you're using the configured logger (not print statements)

### Request ID lost in background tasks
- Use `@with_request_context` decorator
- For Celery, use `@celery_task_with_context()` decorator
- Pass request_id explicitly if decorators can't be used

### Different request IDs in related logs
- Verify you're not creating new threads without context propagation
- Check if async operations are properly awaited
- Use TracingHelper for complex multi-step operations
