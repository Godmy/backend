# Sentry Error Tracking & Monitoring Integration

This document provides a comprehensive guide to the Sentry integration in the МультиПУЛЬТ backend template.

## Overview

Sentry is integrated to provide automatic error tracking, performance monitoring, and comprehensive debugging information for production environments. The integration captures uncaught exceptions, tracks user context, monitors database queries, and provides performance insights.

## Features

### 1. Automatic Error Capture
- All uncaught exceptions are automatically sent to Sentry
- HTTP 5xx errors are tracked
- GraphQL errors are captured
- Database errors are monitored via SQLAlchemy integration

### 2. User Context Tracking
- Automatically captures user information (ID, username, email) for authenticated requests
- Links errors to specific users for better debugging
- User context is cleared on logout

### 3. Performance Monitoring
- Transaction traces for tracking request performance
- Database query performance monitoring
- Configurable sample rates to control overhead
- Support for custom transaction tracking

### 4. Breadcrumbs
- Automatic tracking of user actions leading up to errors
- Authentication events are logged as breadcrumbs
- Custom breadcrumbs can be added for important operations

### 5. Sensitive Data Filtering
Automatically filters the following before sending to Sentry:
- Passwords
- JWT tokens
- API keys
- Authorization headers
- Cookies
- Session tokens
- Any field containing "password", "token", "secret", etc.

### 6. Environment Separation
- Errors are tagged with environment (development, staging, production)
- Different sample rates for different environments
- Release tracking to link errors to specific deployments

## Setup

### 1. Create a Sentry Project

1. Sign up at [sentry.io](https://sentry.io) (free for up to 5,000 errors/month)
2. Create a new project:
   - Platform: **Python**
   - Framework: **Starlette** (or ASGI)
3. Copy the **DSN** from Project Settings → Client Keys

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Sentry Configuration
SENTRY_DSN=https://your-key@o123456.ingest.sentry.io/7654321
ENVIRONMENT=production
SENTRY_ENABLE_TRACING=true
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% for production
SENTRY_RELEASE=backend@1.0.0   # Optional
SENTRY_DEBUG=false
```

**Environment-specific recommendations:**

| Environment | Sample Rate | Tracing | Notes |
|------------|-------------|---------|-------|
| Development | 1.0 (100%) | Enabled | Full monitoring for debugging |
| Staging | 0.5 (50%) | Enabled | Balanced monitoring |
| Production | 0.1 (10%) | Enabled | Low overhead, sufficient data |

### 3. Deploy Configuration

**Docker Compose (Production):**
The `docker-compose.prod.yml` is already configured with Sentry variables. Just set them in your environment:

```bash
export SENTRY_DSN="https://your-key@sentry.io/project"
export ENVIRONMENT="production"
export SENTRY_RELEASE="backend@$(git rev-parse --short HEAD)"
```

**Docker Compose (Development):**
Leave `SENTRY_DSN` empty in `docker-compose.dev.yml` to disable Sentry locally, or set it to test the integration.

## Usage

### Automatic Error Capture

Errors are automatically captured without any code changes:

```python
# This exception will be automatically sent to Sentry
def risky_operation():
    raise ValueError("Something went wrong!")
```

### Manual Error Capture

For better context, manually capture errors:

```python
from core.sentry import capture_exception

try:
    process_payment(user_id=123, amount=100.50)
except Exception as e:
    event_id = capture_exception(
        e,
        user_id=user.id,
        operation="process_payment",
        amount=100.50,
        currency="USD"
    )
    logger.error(f"Payment failed, Sentry event: {event_id}")
```

### Capture Warning Messages

Send non-exception messages to Sentry:

```python
from core.sentry import capture_message

# Warning level
capture_message(
    "User exceeded rate limit",
    level="warning",
    user_id=user.id,
    endpoint="/graphql",
    limit=100
)

# Info level
capture_message(
    "Unusual activity detected",
    level="info",
    user_id=user.id,
    activity_type="multiple_logins"
)
```

### Add Breadcrumbs

Track important user actions:

```python
from core.sentry import add_breadcrumb

# Track navigation
add_breadcrumb("User viewed checkout page", category="navigation")

# Track database operations
add_breadcrumb(
    "User created concept",
    category="database",
    concept_id=concept.id,
    concept_name=concept.name
)

# Track API calls
add_breadcrumb(
    "Called external API",
    category="api",
    endpoint="https://api.example.com/payment",
    status_code=200
)
```

### Performance Monitoring

Track the performance of critical operations:

```python
from core.sentry import start_transaction

def process_order(order_id: int):
    with start_transaction("process_order", op="task") as transaction:
        # Add context
        transaction.set_tag("order_id", order_id)
        transaction.set_tag("priority", "high")

        # Track individual operations as spans
        with transaction.start_child(op="db", description="Load order"):
            order = db.query(Order).get(order_id)

        with transaction.start_child(op="http", description="Process payment"):
            payment_result = payment_gateway.charge(order.total)

        with transaction.start_child(op="db", description="Update order"):
            order.status = "completed"
            db.commit()

        return order
```

### User Context

User context is **automatically set** for authenticated GraphQL requests. You can also manually manage it:

```python
from core.sentry import set_user_context, clear_user_context

# Set user context
set_user_context(
    user_id=user.id,
    username=user.username,
    email=user.email
)

# Clear on logout
clear_user_context()
```

### Custom Context

Add custom context to errors:

```python
from core.sentry import set_context

# Add database context
set_context("database", {
    "query": "SELECT * FROM users WHERE id = ?",
    "duration_ms": 45.2,
    "rows_affected": 1
})

# Add feature flag context
set_context("feature_flags", {
    "new_checkout": True,
    "beta_features": False
})
```

## Integration Points

### 1. Application Startup (app.py)

Sentry is initialized automatically when the application starts:

```python
from core.sentry import init_sentry

# Initialize Sentry (reads config from environment)
init_sentry()
```

### 2. GraphQL Context (app.py)

User context is automatically set for authenticated requests:

```python
class GraphQLWithContext(GraphQL):
    async def get_context(self, request, response=None):
        # ... authentication logic ...

        if user and user.is_active:
            # Set Sentry user context
            set_user_context(
                user_id=user.id,
                username=user.username,
                email=user.email
            )

            # Add breadcrumb
            add_breadcrumb(
                f"Authenticated request from user {user.username}",
                category="auth",
                level="info"
            )
```

### 3. Service Layer

Use manual capture in critical business logic:

```python
# auth/services/auth_service.py
from core.sentry import capture_exception, add_breadcrumb

class AuthService:
    @staticmethod
    def login(username: str, password: str):
        try:
            user = authenticate(username, password)
            add_breadcrumb("User logged in", category="auth", user_id=user.id)
            return user
        except AuthenticationError as e:
            capture_exception(e, username=username, ip_address=request.client.host)
            raise
```

## Sentry Dashboard

### Error Tracking

Navigate to **Issues** in your Sentry project to see:
- List of errors grouped by type
- Error frequency and trends
- Affected users count
- Stack traces with code context
- Breadcrumbs showing user actions
- Request/response data

### Performance Monitoring

Navigate to **Performance** to see:
- Transaction throughput (requests per second)
- Latency percentiles (p50, p75, p95, p99)
- Slow database queries
- External API call performance
- Individual transaction traces

### Releases

Track errors by deployment:
1. Set `SENTRY_RELEASE=backend@v1.2.3` in environment
2. Sentry will group errors by release
3. See which releases introduced new errors
4. Track error resolution across releases

### Alerts

Configure alerts in Sentry UI:
1. **Issue Alerts**: Alert when new errors occur or error frequency spikes
2. **Metric Alerts**: Alert on performance degradation
3. **Integrations**: Send to Slack, email, PagerDuty, etc.

Example alert rules:
- New error first seen
- Error rate exceeds 10/minute
- P95 latency exceeds 1000ms
- More than 5 users affected by same error

## Testing

### Unit Tests

Run Sentry integration tests:

```bash
pytest tests/test_sentry.py -v
```

Tests cover:
- Initialization with/without DSN
- Sensitive data filtering
- User context tracking
- Breadcrumb creation
- Manual error capture
- Configuration options

### Manual Testing

Test Sentry integration in development:

1. Set `SENTRY_DSN` in `.env`
2. Start the application
3. Trigger an error:
   ```python
   # Add to a GraphQL mutation for testing
   raise Exception("Test Sentry integration")
   ```
4. Check Sentry dashboard for the error

## Troubleshooting

### Errors not appearing in Sentry

**Check 1: DSN configured?**
```bash
echo $SENTRY_DSN
```
Should output your DSN, not empty.

**Check 2: Sentry initialized?**
Look for log message on startup:
```
INFO: Sentry initialized successfully for environment: production
```

**Check 3: Sample rate?**
If `SENTRY_TRACES_SAMPLE_RATE=0.1`, only 10% of transactions are sent. Increase for testing.

### Too many events (quota exceeded)

**Solution 1: Reduce sample rate**
```bash
SENTRY_TRACES_SAMPLE_RATE=0.05  # 5%
```

**Solution 2: Filter noisy errors**
In Sentry UI:
1. Go to Project Settings → Inbound Filters
2. Add filters for known errors (e.g., 404s, client errors)

**Solution 3: Adjust quotas**
Upgrade Sentry plan or adjust quota limits in Sentry settings.

### Sensitive data leaked

**Check**: Review `core/sentry.py` → `filter_sensitive_data()`

Add custom filtering:
```python
def filter_sensitive_data(event, hint):
    # Add custom sensitive keys
    SENSITIVE_KEYS.extend(["ssn", "credit_card", "api_secret"])

    # ... rest of filter logic ...
```

### Performance overhead

**Solution 1: Disable tracing in production**
```bash
SENTRY_ENABLE_TRACING=false
```

**Solution 2: Lower sample rate**
```bash
SENTRY_TRACES_SAMPLE_RATE=0.05  # 5%
```

**Solution 3: Disable in development**
```bash
SENTRY_DSN=  # Leave empty
```

## Best Practices

### 1. Use Environments
Always set `ENVIRONMENT` to separate dev/staging/production errors:
```bash
ENVIRONMENT=production
```

### 2. Tag Errors Properly
Add relevant tags for filtering:
```python
transaction.set_tag("feature", "checkout")
transaction.set_tag("user_type", "premium")
```

### 3. Add Context, Not PII
Include useful debugging info, but avoid sensitive data:
```python
# Good
capture_exception(e, order_id=order.id, order_total=order.total)

# Bad
capture_exception(e, credit_card=card.number)  # Will be filtered anyway
```

### 4. Use Release Tracking
Link errors to deployments:
```bash
export SENTRY_RELEASE="backend@$(git describe --tags --always)"
```

### 5. Set Up Alerts
Don't wait to check Sentry - configure alerts to notify you immediately.

### 6. Review Weekly
Schedule weekly reviews of:
- New error types
- Error frequency trends
- Performance regressions
- User impact

### 7. Clean Up Old Issues
Mark resolved issues as resolved in Sentry to keep the dashboard clean.

## Cost Optimization

Sentry free tier includes:
- 5,000 errors per month
- 10,000 performance units per month
- 30-day data retention

To stay within limits:

1. **Filter client errors**: Don't track 4xx errors
2. **Sample aggressively in production**: 5-10% is usually enough
3. **Disable tracing in non-critical environments**
4. **Use error grouping**: Sentry automatically groups similar errors
5. **Resolve old issues**: Reduces noise and counts

## Security Considerations

1. **Sensitive Data Filtering**: Always enabled, review `core/sentry.py`
2. **DSN Protection**: Keep `SENTRY_DSN` secret (it's like an API key)
3. **User Privacy**: Only send user ID, username, email - no PII
4. **HTTPS Only**: Sentry SDK enforces HTTPS for all communications
5. **Data Retention**: Set retention limits in Sentry project settings

## Further Reading

- [Sentry Python SDK Documentation](https://docs.sentry.io/platforms/python/)
- [Sentry Performance Monitoring](https://docs.sentry.io/product/performance/)
- [Sentry Best Practices](https://docs.sentry.io/product/best-practices/)
- [Sentry Pricing](https://sentry.io/pricing/)

## Support

For issues with this integration:
1. Check this documentation
2. Review `core/sentry.py` implementation
3. Check Sentry Python SDK docs
4. Open an issue in the project repository
