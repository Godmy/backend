# Database Connection Pool Monitoring

Prometheus metrics for monitoring SQLAlchemy connection pool health and usage.

## Features

- Real-time connection pool statistics
- Prometheus-compatible metrics
- Automatic updates on /metrics endpoint scrape
- No performance impact (reads existing pool state)
- Alerts for pool exhaustion

## Available Metrics

- `db_pool_size` - Total connection pool size
- `db_pool_checked_out` - Active connections (in use)
- `db_pool_checked_in` - Available connections (idle)
- `db_pool_overflow` - Current overflow connections
- `db_pool_num_overflow` - Maximum overflow connections allowed

## Prometheus Query Examples

### Connection Pool Usage Percentage

```promql
# Connection pool usage percentage
(db_pool_checked_out / db_pool_size) * 100
```

### Available Connections

```promql
# Available connections
db_pool_checked_in
```

### Pool Exhaustion Alert

```promql
# Pool exhaustion alert (over 90% usage)
(db_pool_checked_out / db_pool_size) > 0.9
```

### Overflow Connection Usage

```promql
# Current overflow connections
db_pool_overflow

# Overflow connections as percentage of max
(db_pool_overflow / db_pool_num_overflow) * 100
```

## Implementation

- `core/metrics.py` - Prometheus metrics and `update_db_pool_metrics()` function
- `app.py` - Automatic update on /metrics endpoint
- Metrics updated on every Prometheus scrape (typically every 15s)

## Database Configuration

```python
# core/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=5,           # Base pool size
    max_overflow=10,       # Additional connections when pool exhausted
    pool_pre_ping=True,    # Verify connections before use
    pool_recycle=3600      # Recycle connections after 1 hour
)
```

### Configuration Parameters

- **pool_size**: Base number of connections kept in pool (default: 5)
- **max_overflow**: Additional connections when pool exhausted (default: 10)
- **pool_pre_ping**: Test connection before use (recommended: True)
- **pool_recycle**: Recycle connections after N seconds (recommended: 3600)
- **pool_timeout**: Seconds to wait for connection (default: 30)

## Grafana Dashboard Panels

### 1. Connection Pool Usage (%)

**Metric:**
```promql
(db_pool_checked_out / db_pool_size) * 100
```

**Visualization:** Gauge
**Unit:** Percent (0-100)
**Thresholds:**
- Green: 0-70%
- Yellow: 70-90%
- Red: 90-100%

### 2. Active vs Available Connections

**Metrics:**
```promql
db_pool_checked_out
db_pool_checked_in
```

**Visualization:** Time series
**Unit:** Connections
**Legend:** Show as table

### 3. Overflow Connections

**Metric:**
```promql
db_pool_overflow
```

**Visualization:** Counter
**Unit:** Connections
**Alert:** > 0 for extended period

### 4. Pool Exhaustion Events

**Alert Rule:**
```yaml
- alert: DatabasePoolExhaustion
  expr: (db_pool_checked_out / db_pool_size) > 0.9
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Database connection pool nearly exhausted"
    description: "Pool usage is {{ $value | humanizePercentage }}"
```

## Monitoring Best Practices

### Alert Configuration

#### Critical Alerts

```yaml
# Pool usage over 90%
- alert: HighPoolUsage
  expr: (db_pool_checked_out / db_pool_size) > 0.9
  for: 5m
  severity: critical

# Pool completely exhausted
- alert: PoolExhausted
  expr: db_pool_checked_in == 0
  for: 1m
  severity: critical

# Using overflow connections
- alert: UsingOverflow
  expr: db_pool_overflow > 0
  for: 10m
  severity: warning
```

#### Warning Alerts

```yaml
# Pool usage over 70%
- alert: MediumPoolUsage
  expr: (db_pool_checked_out / db_pool_size) > 0.7
  for: 15m
  severity: warning

# Sustained high usage
- alert: SustainedHighUsage
  expr: avg_over_time(db_pool_checked_out[1h]) > (db_pool_size * 0.8)
  for: 1h
  severity: warning
```

### Metrics to Track

1. **Pool utilization** - Track usage patterns over time
2. **Peak usage** - Identify traffic spikes
3. **Overflow frequency** - How often pool is exhausted
4. **Connection acquisition time** - Time to get connection from pool
5. **Connection lifetime** - How long connections are held

### Troubleshooting

#### High Pool Usage

**Symptoms:**
- Pool usage consistently > 80%
- Slow API responses
- Connection timeout errors

**Solutions:**
```python
# Increase pool size
engine = create_engine(
    DATABASE_URL,
    pool_size=10,  # Increase from 5
    max_overflow=20  # Increase from 10
)
```

#### Connection Leaks

**Symptoms:**
- `db_pool_checked_out` never decreasing
- Pool exhaustion during low traffic

**Detection:**
```python
# Log long-held connections
from sqlalchemy import event

@event.listens_for(Engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    connection_record.checkout_time = time.time()

@event.listens_for(Engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    duration = time.time() - connection_record.checkout_time
    if duration > 60:  # Held for more than 60 seconds
        logger.warning(f"Connection held for {duration}s")
```

**Solutions:**
- Use context managers for sessions
- Ensure all queries are committed/rolled back
- Close sessions explicitly in exception handlers

#### Overflow Usage

**Symptoms:**
- `db_pool_overflow` > 0 regularly
- Variable response times

**Analysis:**
```promql
# How often are we using overflow?
rate(db_pool_overflow[5m]) > 0
```

**Solutions:**
- Increase base pool size
- Optimize slow queries
- Add read replicas for read-heavy workloads
- Implement connection pooling at application level

## Query Optimization

### Find Connection-Heavy Operations

```python
from core.metrics import db_query_duration_seconds
import time

def track_query(query_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            db_query_duration_seconds.labels(operation=query_name).observe(duration)
            return result
        return wrapper
    return decorator

@track_query("get_user_with_roles")
def get_user_with_roles(user_id):
    # Query implementation
    pass
```

### Monitor Query Duration

```promql
# Slowest queries
topk(10, rate(db_query_duration_seconds_sum[5m]) / rate(db_query_duration_seconds_count[5m]))

# P95 query duration
histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))
```

## Capacity Planning

### Calculate Required Pool Size

```python
# Formula: pool_size = (avg_concurrent_requests * avg_query_time) + buffer

# Example:
# - 100 req/s average traffic
# - 50ms average query time
# - 20% buffer

concurrent_queries = 100 * 0.05  # 5 queries
buffer = concurrent_queries * 0.2  # 1 query
required_pool_size = int(concurrent_queries + buffer)  # 6 connections

print(f"Recommended pool_size: {required_pool_size}")
```

### Load Testing

```python
# Test pool under load
import asyncio
from sqlalchemy.orm import Session

async def stress_test():
    tasks = []
    for i in range(100):  # Simulate 100 concurrent requests
        tasks.append(query_database())

    await asyncio.gather(*tasks)

async def query_database():
    session = Session(engine)
    try:
        # Perform queries
        result = session.query(User).all()
    finally:
        session.close()

# Monitor pool metrics during test
# Expected: pool_checked_out should not exceed pool_size + max_overflow
```

## Environment-Specific Configuration

### Development

```python
# Small pool for local development
engine = create_engine(
    DATABASE_URL,
    pool_size=2,
    max_overflow=5,
    pool_pre_ping=True
)
```

### Staging

```python
# Medium pool for staging
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### Production

```python
# Large pool for production
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
    echo_pool=False  # Disable pool logging
)
```

## Related Documentation

- [Prometheus Metrics](prometheus.md) - Overview of all metrics
- [Request Logging](request_logging.md) - Request tracking
- [Performance Optimization](../PERFORMANCE.md) - General optimization guide
