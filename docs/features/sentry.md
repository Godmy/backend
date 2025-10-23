# Error Tracking & Monitoring (Sentry)

Comprehensive error tracking and performance monitoring with Sentry integration.

## Features

- Automatic capture of all uncaught exceptions
- Performance monitoring with transaction traces
- User context tracking (user_id, username, email)
- Request context (endpoint, method, headers)
- Breadcrumbs for tracking user actions
- Sensitive data filtering (passwords, tokens)
- Release tracking for linking errors to deployments
- Environment separation (dev/staging/production)
- SQLAlchemy query performance tracking
- Configurable sample rates for performance monitoring

## Setup

### 1. Create Sentry Project

- Sign up at [sentry.io](https://sentry.io)
- Create a new project (Python/Starlette)
- Copy the DSN from project settings

### 2. Configure Environment Variables

```bash
# .env
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENVIRONMENT=production
SENTRY_ENABLE_TRACING=true
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% in production
SENTRY_RELEASE=backend@1.0.0  # Optional, for release tracking
```

### 3. Automatic Capture

Sentry automatically captures:
- Uncaught exceptions
- Database errors
- HTTP 500 errors
- GraphQL errors

## Manual Error Capture

### Capture Exceptions

```python
from core.sentry import capture_exception, capture_message, add_breadcrumb

# Capture exception with context
try:
    process_payment(user_id=123, amount=100)
except Exception as e:
    event_id = capture_exception(e, user_id=123, operation="payment", amount=100)
    logger.error(f"Payment failed, Sentry event: {event_id}")
```

### Capture Messages

```python
# Capture warning message
capture_message("User exceeded rate limit", level="warning", user_id=123)
```

### Add Breadcrumbs

```python
# Add breadcrumb for tracking user actions
add_breadcrumb("User clicked checkout button", category="navigation", user_id=123)
```

## Performance Monitoring

Track performance of specific operations:

```python
from core.sentry import start_transaction

# Track performance of operations
with start_transaction("process_order", op="task") as transaction:
    transaction.set_tag("user_id", user.id)
    transaction.set_data("order_id", order.id)
    # Do work
    process_order(order)
```

## User Context

User context is automatically set when a user is authenticated. You can also manually set it:

```python
from core.sentry import set_user_context, clear_user_context

# Set user context
set_user_context(user_id=123, username="john_doe", email="john@example.com")

# Clear on logout
clear_user_context()
```

## Sensitive Data Filtering

The following data is automatically filtered before sending to Sentry:
- Passwords
- JWT tokens
- API keys
- Authorization headers
- Cookies
- Any field containing "password", "token", "secret", etc.

## Implementation

- `core/sentry.py` - Sentry initialization and utilities
- `app.py` - Automatic initialization on startup
- Integrations: Starlette, SQLAlchemy, Logging
- Filter function: `before_send()` removes sensitive data

## Production Recommendations

### Performance
- Set `SENTRY_TRACES_SAMPLE_RATE=0.1` (10%) to reduce overhead
- Enable release tracking with `SENTRY_RELEASE`
- Monitor transaction volume to avoid quota limits

### Alerts
- Configure alerts in Sentry UI for critical errors
- Set up Slack/email notifications
- Create custom alert rules for business-critical flows
- Use anomaly detection for unusual error patterns

### Error Management
- Review error grouping and ignore non-critical errors
- Set up issue assignment and workflows
- Use release tracking to identify problematic deployments
- Configure error retention policies

### Best Practices
- Tag errors with environment, version, and feature flags
- Use breadcrumbs to track user flows
- Set appropriate sampling rates per environment
- Monitor Sentry quota usage
- Regularly review and resolve errors

## Environment Configuration

### Development
```bash
SENTRY_DSN=your_dev_dsn
ENVIRONMENT=development
SENTRY_ENABLE_TRACING=true
SENTRY_TRACES_SAMPLE_RATE=1.0  # 100% for testing
```

### Staging
```bash
SENTRY_DSN=your_staging_dsn
ENVIRONMENT=staging
SENTRY_ENABLE_TRACING=true
SENTRY_TRACES_SAMPLE_RATE=0.5  # 50%
```

### Production
```bash
SENTRY_DSN=your_prod_dsn
ENVIRONMENT=production
SENTRY_ENABLE_TRACING=true
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10%
SENTRY_RELEASE=backend@1.0.0
```

## Troubleshooting

### Sentry not capturing errors
- Verify DSN is correct
- Check network connectivity
- Verify Sentry SDK is initialized
- Check if errors are filtered

### Too many events
- Reduce sample rate
- Add more filters to `before_send()`
- Ignore known/non-critical errors
- Use rate limiting in Sentry UI

### Missing context
- Ensure user context is set after authentication
- Add breadcrumbs at key points
- Use transactions for complex operations
- Tag events with relevant metadata

## Related Documentation

- [Sentry Official Docs](https://docs.sentry.io/)
- [Python SDK Reference](https://docs.sentry.io/platforms/python/)
- [Performance Monitoring](https://docs.sentry.io/product/performance/)
