# API Request/Response Logging

Comprehensive logging of all API requests and responses for debugging and monitoring.

## Features

- Logs all HTTP requests (method, path, headers, body)
- Logs all responses (status, duration)
- Generates unique request ID for tracing
- Extracts user ID from JWT token
- Masks sensitive data (passwords, tokens, secrets)
- Configurable logging levels
- Request duration tracking
- X-Request-ID header in responses

## Example Log Output

```
INFO: [req-abc123] POST /graphql 200 (125ms) user_id=42
INFO: [req-abc123] GET /api/users 200 (15ms) user_id=42 body={"username": "john"}
WARNING: [req-def456] POST /auth/login 401 (89ms)
ERROR: [req-ghi789] GET /api/orders 500 (2341ms) user_id=42
```

## Configuration

### In Code (app.py)

```python
app.add_middleware(
    RequestLoggingMiddleware,
    log_body=True,        # Log request/response bodies
    log_headers=False     # Log headers (can expose secrets!)
)
```

### Environment Variables

```bash
# .env
REQUEST_LOGGING_ENABLED=true
REQUEST_LOGGING_BODY=true
REQUEST_LOGGING_HEADERS=false  # DON'T enable in production (leaks secrets)
REQUEST_LOGGING_LEVEL=INFO
```

## Logging Levels

Different log levels by status code:
- **2xx** → INFO (successful requests)
- **4xx** → WARNING (client errors)
- **5xx** → ERROR (server errors)

## Features Detail

### User ID Extraction

Automatically extracts user ID from JWT token:

```python
# Looks for Authorization header
Authorization: Bearer <jwt_token>

# Extracts user_id from token claims
# Includes in all log statements
```

### Sensitive Data Masking

The following fields are automatically masked:
- password
- token
- secret
- authorization
- api_key
- access_token
- refresh_token
- cookie

Masked value: `***REDACTED***`

### Request Duration

Tracks time from request start to response:
```
POST /graphql 200 (125ms)  # 125 milliseconds
```

### Request ID

Unique ID generated for each request:
- Format: `req-<uuid>`
- Included in logs: `[req-abc123]`
- Returned in response header: `X-Request-ID: req-abc123`
- Used for distributed tracing

## Implementation

- `core/middleware/request_logging.py` - RequestLoggingMiddleware
- `app.py` - Automatically enabled
- Masks fields: password, token, secret, authorization, api_key, access_token, refresh_token

## Use Cases

### Debugging Customer Issues

1. Customer reports error at specific time
2. Search logs by timestamp
3. Find request ID from logs
4. Trace entire request flow with request ID
5. Identify root cause

### API Usage Analytics

```bash
# Count requests by endpoint
grep "POST /graphql" application.log | wc -l

# Find slow requests
grep "graphql" application.log | grep -E "\([0-9]{4,}ms\)"

# Count errors by user
grep "user_id=42" application.log | grep "ERROR" | wc -l
```

### Security Auditing

```bash
# Find failed login attempts
grep "POST /auth/login" application.log | grep "401"

# Track user activity
grep "user_id=42" application.log | grep "POST"

# Detect brute force attempts
grep "401" application.log | cut -d' ' -f6 | sort | uniq -c | sort -rn
```

### Performance Monitoring

```bash
# Find slowest endpoints
grep -E "\([0-9]{3,}ms\)" application.log | sort -t'(' -k2 -rn | head -10

# Average response time for endpoint
grep "POST /graphql" application.log | grep -oE "\([0-9]+ms\)" | grep -oE "[0-9]+" | awk '{sum+=$1; count++} END {print sum/count "ms"}'
```

## Best Practices

### What to Log

✅ **Do log:**
- Request method and path
- Response status code
- Request duration
- User ID (if authenticated)
- Request ID for tracing
- Error messages

❌ **Don't log:**
- Passwords (auto-masked)
- API keys (auto-masked)
- Personal identifiable information (PII)
- Credit card numbers
- Raw authorization headers

### Production Settings

```bash
# Recommended production configuration
REQUEST_LOGGING_ENABLED=true
REQUEST_LOGGING_BODY=false  # Disable body logging in prod
REQUEST_LOGGING_HEADERS=false  # NEVER enable in production
REQUEST_LOGGING_LEVEL=INFO
```

### Log Retention

```bash
# Rotate logs daily
/var/log/application.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

## Integration with Other Systems

### Sentry

Request ID automatically included in Sentry errors:
```python
from core.sentry import capture_exception
from core.context import get_request_id

try:
    process_request()
except Exception as e:
    capture_exception(e, extra={"request_id": get_request_id()})
```

### Prometheus

Request metrics automatically collected:
```python
http_requests_total.labels(method="POST", endpoint="/graphql", status=200).inc()
http_request_duration_seconds.labels(method="POST", endpoint="/graphql").observe(0.125)
```

### ELK Stack

Format logs as JSON for easier parsing:
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": record.created,
            "level": record.levelname,
            "request_id": getattr(record, "request_id", None),
            "user_id": getattr(record, "user_id", None),
            "message": record.getMessage()
        })
```

## Troubleshooting

### Logs are too verbose

Reduce log level or disable body logging:
```bash
REQUEST_LOGGING_BODY=false
REQUEST_LOGGING_LEVEL=WARNING
```

### Sensitive data in logs

Verify masking is working:
```bash
# Should not find passwords
grep "password" application.log | grep -v "REDACTED"
```

Add more fields to mask:
```python
# In RequestLoggingMiddleware
SENSITIVE_FIELDS = [
    "password", "token", "secret",
    "credit_card", "ssn"  # Add custom fields
]
```

### Request ID not in logs

Verify middleware is enabled:
```python
# In app.py
app.add_middleware(RequestLoggingMiddleware)
```

### Performance impact

Minimize logging in hot paths:
```python
# Disable body logging for performance
REQUEST_LOGGING_BODY=false

# Only log errors
REQUEST_LOGGING_LEVEL=ERROR
```

## Log Analysis Tools

### Grep Examples

```bash
# Find all errors for user
grep "user_id=42" application.log | grep "ERROR"

# Find slow requests (>1 second)
grep -E "\([0-9]{4,}ms\)" application.log

# Count requests by endpoint
grep -oE "(GET|POST|PUT|DELETE) [^ ]+" application.log | sort | uniq -c

# Find requests by request ID
grep "req-abc123" application.log
```

### awk Examples

```bash
# Calculate average response time
awk -F'[()]' '{if ($2 ~ /ms/) sum+=substr($2,1,length($2)-2); count++} END {print sum/count "ms"}' application.log

# Group by status code
awk '{print $4}' application.log | sort | uniq -c
```

### Python Analysis

```python
import re
from collections import Counter

# Parse log file
with open('application.log') as f:
    lines = f.readlines()

# Count status codes
status_codes = Counter()
for line in lines:
    match = re.search(r' (\d{3}) ', line)
    if match:
        status_codes[match.group(1)] += 1

print(status_codes)
# Counter({'200': 1523, '404': 42, '500': 8})
```

## Related Documentation

- [Request Tracing](request_tracing.md) - Distributed request tracking
- [Prometheus Metrics](prometheus.md) - Request metrics collection
- [Sentry Integration](sentry.md) - Error tracking with request context
