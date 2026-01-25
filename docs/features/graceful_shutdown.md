# Graceful Shutdown Handling

Ensures the application shuts down gracefully without interrupting active requests.

## Features

- Signal handlers for SIGTERM (Docker, K8s) and SIGINT (Ctrl+C)
- Waits for active requests to complete (configurable timeout)
- Rejects new requests during shutdown (returns 503)
- Closes database connections gracefully
- Closes Redis connections
- Flushes logs
- Health checks return 503 during shutdown
- Cross-platform support (Unix and Windows)

## Configuration

### Environment Variables

```bash
# .env
SHUTDOWN_TIMEOUT=30  # Maximum seconds to wait for requests (default: 30)
```

### Python Configuration

```python
# app.py
from core.shutdown import GracefulShutdown

shutdown_handler = GracefulShutdown(
    timeout=30,
    on_shutdown=[
        close_database_connections,
        close_redis_connections,
        flush_logs
    ]
)
```

## Implementation

- `core/shutdown.py` - GracefulShutdown handler with signal management
- `core/middleware/shutdown.py` - ShutdownMiddleware (rejects requests during shutdown)
- `app.py` - Automatically configured on startup

## How It Works

### Shutdown Sequence

1. Application receives SIGTERM/SIGINT signal
2. Shutdown handler sets `is_shutting_down` flag
3. New requests are rejected with 503 status
4. Active requests complete (up to `SHUTDOWN_TIMEOUT` seconds)
5. Custom shutdown callbacks run (if configured)
6. Database connections closed
7. Redis connections closed
8. Logs flushed
9. Application exits cleanly

### State Diagram

```
Running → Signal Received → Draining → Closing Resources → Stopped
   ↓           ↓              ↓              ↓              ↓
Accept     Set flag      Wait for     Close DB/Redis    Exit
requests   Reject new    active       Flush logs        process
           requests      requests
```

## Testing Shutdown

### Local Testing

```bash
# Start application
python app.py

# Send SIGTERM signal (in another terminal)
kill -TERM <pid>

# Or press Ctrl+C
```

### Expected Log Output

```
INFO: Received SIGTERM signal, initiating graceful shutdown...
INFO: Rejecting new requests...
INFO: Waiting up to 30s for active requests to complete...
INFO: 3 active requests remaining...
INFO: 1 active requests remaining...
INFO: All active requests completed
INFO: Closing database connections...
INFO: Database connections closed
INFO: Closing Redis connections...
INFO: Redis connections closed
INFO: Flushing logs...
INFO: Graceful shutdown completed successfully
```

### Docker Testing

```bash
# Start container
docker run -d --name test-app your-image

# Send SIGTERM
docker stop test-app

# View logs
docker logs test-app
```

### Kubernetes Testing

```bash
# Delete pod (triggers SIGTERM)
kubectl delete pod your-pod

# View logs
kubectl logs your-pod --previous
```

## Production Deployment

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11

# Install signal handling dependencies
RUN apt-get update && apt-get install -y tini

# Use tini as init system for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["python", "app.py"]
```

### Docker Compose

```yaml
# docker-compose.yml
services:
  app:
    image: your-app
    stop_grace_period: 30s  # Should match SHUTDOWN_TIMEOUT
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
```

### Kubernetes Configuration

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: app
        image: your-app
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      terminationGracePeriodSeconds: 30  # Should match SHUTDOWN_TIMEOUT
```

## Advanced Usage

### Custom Shutdown Callbacks

```python
from core.shutdown import GracefulShutdown

def cleanup_temp_files():
    """Clean up temporary files"""
    import os
    import glob
    for f in glob.glob("/tmp/app-*"):
        os.remove(f)

def send_shutdown_metrics():
    """Send metrics about shutdown"""
    from core.metrics import app_shutdowns_total
    app_shutdowns_total.inc()

shutdown_handler = GracefulShutdown(
    timeout=30,
    on_shutdown=[
        close_database_connections,
        close_redis_connections,
        cleanup_temp_files,
        send_shutdown_metrics,
        flush_logs
    ]
)
```

### Async Shutdown Callbacks

```python
async def async_cleanup():
    """Async cleanup operations"""
    await redis_client.close()
    await http_client.close()

shutdown_handler = GracefulShutdown(
    timeout=30,
    on_shutdown=[
        lambda: asyncio.run(async_cleanup()),
        close_database_connections
    ]
)
```

### Conditional Shutdown

```python
def shutdown_if_healthy():
    """Only shutdown if health checks pass"""
    from core.health import health_check
    if health_check():
        return True
    logger.warning("Health check failed, delaying shutdown")
    return False

shutdown_handler = GracefulShutdown(
    timeout=30,
    pre_shutdown_check=shutdown_if_healthy
)
```

## Monitoring

### Metrics

```python
# core/metrics.py
from prometheus_client import Counter, Histogram

app_shutdowns_total = Counter(
    'app_shutdowns_total',
    'Total number of application shutdowns',
    ['reason']
)

shutdown_duration_seconds = Histogram(
    'shutdown_duration_seconds',
    'Time taken to shutdown',
    buckets=[5, 10, 15, 20, 25, 30]
)
```

### Logging

```python
# Log shutdown events
logger.info("Shutdown initiated", extra={
    "reason": "SIGTERM",
    "active_requests": 5,
    "timeout": 30
})

logger.info("Shutdown completed", extra={
    "duration": 12.5,
    "reason": "SIGTERM"
})
```

### Alerts

```yaml
# Prometheus alert rules
groups:
  - name: shutdown_alerts
    rules:
      - alert: FrequentShutdowns
        expr: rate(app_shutdowns_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Application restarting frequently"

      - alert: SlowShutdown
        expr: shutdown_duration_seconds > 25
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Application taking too long to shutdown"
```

## Troubleshooting

### Shutdown Timeout

**Symptom:** Application killed before graceful shutdown completes

**Causes:**
- Long-running requests
- Database connection leaks
- Blocked I/O operations

**Solutions:**
```python
# Increase timeout
SHUTDOWN_TIMEOUT=60

# Add request timeout
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=30)
        except asyncio.TimeoutError:
            return Response("Request timeout", status_code=504)
```

### Requests Failing During Shutdown

**Symptom:** 503 errors during deployment

**Causes:**
- Load balancer not detecting unhealthy instance
- Health check not returning 503 during shutdown

**Solutions:**
```python
# Update health check
@app.get("/health")
def health():
    from core.shutdown import is_shutting_down
    if is_shutting_down():
        return Response(
            {"status": "shutting_down"},
            status_code=503
        )
    return {"status": "healthy"}
```

### Database Connections Not Closing

**Symptom:** Database connections remain open after shutdown

**Causes:**
- Sessions not closed properly
- Connection pool not disposed

**Solutions:**
```python
def close_database_connections():
    from core.database import engine, SessionLocal

    # Close all active sessions
    SessionLocal.close_all()

    # Dispose connection pool
    engine.dispose()

    logger.info("Database connections closed")
```

### Zombie Processes

**Symptom:** Process doesn't exit after shutdown

**Causes:**
- Background threads not joining
- Signal handlers not returning
- Deadlock in cleanup code

**Solutions:**
```python
# Use daemon threads
import threading

thread = threading.Thread(target=background_task, daemon=True)
thread.start()

# Set timeout for thread joins
thread.join(timeout=5)
if thread.is_alive():
    logger.warning("Thread did not terminate in time")
```

## Best Practices

### Do's

✅ **Set appropriate timeout** - Based on longest expected request
✅ **Monitor shutdown duration** - Alert on slow shutdowns
✅ **Test shutdown locally** - Before deploying to production
✅ **Use health checks** - For load balancer integration
✅ **Log shutdown events** - For debugging and monitoring
✅ **Close resources properly** - Database, Redis, file handles
✅ **Use init system** - Tini or dumb-init for Docker

### Don'ts

❌ **Don't ignore signals** - Always handle SIGTERM gracefully
❌ **Don't set timeout too low** - Risk killing active requests
❌ **Don't block shutdown** - Keep cleanup code fast
❌ **Don't forget Redis** - Close all external connections
❌ **Don't skip testing** - Test shutdown in staging first
❌ **Don't rely on SIGKILL** - Should never reach forced kill

## Platform-Specific Notes

### Docker

- Uses SIGTERM for `docker stop`
- Waits 10 seconds by default before SIGKILL
- Configure with `stop_grace_period` in docker-compose
- Use init system (tini) for proper signal handling

### Kubernetes

- Uses SIGTERM for pod termination
- Waits for `terminationGracePeriodSeconds` (default: 30s)
- Removes pod from service endpoints before SIGTERM
- Health checks should return 503 during shutdown

### AWS ECS

- Uses SIGTERM for task termination
- Default timeout: 30 seconds
- Configure with `stopTimeout` in task definition
- Health checks control load balancer deregistration

### Systemd

- Uses SIGTERM for service stop
- Configure timeout with `TimeoutStopSec`
- Logs visible in journalctl
- Can configure custom signals

## Related Documentation

- [Request Logging](request_logging.md) - Log active requests during shutdown
- [Prometheus Metrics](prometheus.md) - Monitor shutdown metrics
- [Health Checks](../CLAUDE.md#health-checks) - Health check configuration
