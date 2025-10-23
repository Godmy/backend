# Prometheus Metrics Collection

Comprehensive metrics collection for monitoring application performance, resource usage, and business logic.

## Features

- Automatic HTTP request tracking (count, duration, in-progress)
- System metrics (CPU, memory, file descriptors)
- Ready-to-use metrics for GraphQL, database, Redis
- Business logic metrics (registrations, emails, file uploads)
- Prometheus-compatible exposition format
- Path normalization for better grouping

## Access Metrics

```bash
curl http://localhost:8000/metrics
```

## Available Metrics

### HTTP Metrics (Auto-collected)

- `http_requests_total` - Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_in_progress` - Current in-flight requests

### System Metrics (Auto-collected)

- `process_cpu_usage_percent` - CPU usage
- `process_memory_bytes` - Memory consumption
- `process_open_fds` - Open file descriptors

### GraphQL Metrics (Ready to use)

- `graphql_query_duration_seconds` - Query execution time
- `graphql_query_errors_total` - Query errors by type

### Database Metrics (Ready to use)

- `db_connections_active` - Active database connections
- `db_query_duration_seconds` - Query execution time
- `db_errors_total` - Database errors

### Business Logic Metrics (Ready to use)

- `users_registered_total` - User registrations by method
- `emails_sent_total` - Emails sent by type and status
- `files_uploaded_total` - Files uploaded by type

## Usage in Services

### Track User Registration

```python
from core.metrics import users_registered_total

# Track user registration
users_registered_total.labels(method='google').inc()
```

### Track Email Sending

```python
from core.metrics import emails_sent_total

# Track email sending
emails_sent_total.labels(email_type='verification', status='success').inc()
```

### Track File Upload

```python
from core.metrics import files_uploaded_total

# Track file upload
files_uploaded_total.labels(file_type='avatar').inc()
```

### Track Database Queries

```python
from core.metrics import db_query_duration_seconds
import time

start_time = time.time()
# ... execute query ...
duration = time.time() - start_time
db_query_duration_seconds.labels(operation='select').observe(duration)
```

### Track GraphQL Operations

```python
from core.metrics import graphql_query_duration_seconds, graphql_query_errors_total
import time

start_time = time.time()
try:
    # ... execute query ...
    duration = time.time() - start_time
    graphql_query_duration_seconds.labels(operation='getConcepts').observe(duration)
except Exception as e:
    graphql_query_errors_total.labels(error_type=type(e).__name__).inc()
    raise
```

## Implementation

- `core/metrics.py` - All metrics definitions
- `core/middleware/metrics.py` - Automatic HTTP metrics collection
- `app.py` - Metrics endpoint registration
- `tests/test_metrics.py` - Comprehensive test suite

## Prometheus Configuration

### Scrape Configuration

```yaml
scrape_configs:
  - job_name: 'multipult-backend'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
```

### Alert Rules

```yaml
groups:
  - name: backend_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} requests/second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds"

      - alert: DatabaseConnectionPoolExhaustion
        expr: db_pool_checked_out / db_pool_size > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "Pool usage is {{ $value | humanizePercentage }}"
```

## Grafana Dashboard

### Key Panels to Create

#### 1. Request Rate
- Metric: `rate(http_requests_total[5m])`
- Visualization: Time series
- Unit: requests/second

#### 2. Error Rate
- Metric: `rate(http_requests_total{status=~"5.."}[5m])`
- Visualization: Time series
- Unit: errors/second

#### 3. Response Time Percentiles
- Metrics:
  - p50: `histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))`
  - p95: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
  - p99: `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))`
- Visualization: Time series
- Unit: seconds

#### 4. Memory Usage
- Metric: `process_memory_bytes`
- Visualization: Gauge
- Unit: bytes

#### 5. CPU Usage
- Metric: `process_cpu_usage_percent`
- Visualization: Gauge
- Unit: percent

#### 6. Database Connection Pool
- Metrics:
  - Active: `db_pool_checked_out`
  - Available: `db_pool_checked_in`
  - Total: `db_pool_size`
- Visualization: Time series
- Unit: connections

#### 7. User Registrations
- Metric: `rate(users_registered_total[1h])`
- Visualization: Time series
- Unit: registrations/hour

#### 8. Email Delivery Status
- Metric: `emails_sent_total`
- Visualization: Bar gauge
- Labels: status (success, failure)

### Example Dashboard JSON

```json
{
  "dashboard": {
    "title": "Backend Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ],
        "type": "timeseries"
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
          }
        ],
        "type": "timeseries"
      },
      {
        "title": "Response Time (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ],
        "type": "timeseries"
      }
    ]
  }
}
```

## Best Practices

### Metric Naming
- Use descriptive names: `http_requests_total` not `requests`
- Include units in name: `_seconds`, `_bytes`, `_total`
- Use consistent prefixes: `http_`, `db_`, `graphql_`

### Labels
- Use low-cardinality labels (avoid user IDs, timestamps)
- Keep label count reasonable (< 10 per metric)
- Use consistent label names across metrics

### Performance
- Don't create metrics in hot paths without caching
- Use histograms for distributions (response times)
- Use counters for totals (request count)
- Use gauges for current values (memory usage)

### Monitoring
- Set up alerts for critical metrics
- Monitor metric cardinality to avoid explosion
- Review metrics regularly and remove unused ones
- Document custom metrics in code comments

## Troubleshooting

### Metrics endpoint returns 404
- Verify endpoint is registered in `app.py`
- Check if metrics middleware is enabled
- Verify Prometheus client is installed

### Metrics not updating
- Verify metrics are being incremented/observed in code
- Check if middleware is properly initialized
- Look for exceptions in metric collection code

### High cardinality warnings
- Review label usage (avoid user IDs, UUIDs)
- Aggregate high-cardinality labels
- Remove unused labels
- Use relabeling in Prometheus config

### Missing metrics
- Verify metric is defined in `core/metrics.py`
- Check if metric is imported where used
- Verify metric type matches usage (counter vs gauge)
- Check for typos in metric names

## Related Documentation

- [Prometheus Official Docs](https://prometheus.io/docs/)
- [Python Client Library](https://github.com/prometheus/client_python)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [Best Practices](https://prometheus.io/docs/practices/naming/)
