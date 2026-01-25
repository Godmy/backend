# Audit Logging System

Comprehensive audit logging system for tracking all important user actions and system events.

## Features

- Automatic logging of authentication events (login, logout, register, OAuth)
- Entity CRUD operation tracking
- IP address and User-Agent capture
- Before/after data snapshots (JSON)
- Admin and user-level queries
- Activity statistics
- Automatic cleanup of old logs

## GraphQL API

See [docs/graphql/query/audit.md](../graphql/query/audit.md) for complete API documentation with examples.

## Logged Actions

### Authentication Events
- `login` - User login (password or OAuth)
- `logout` - User logout
- `register` - New user registration
- `oauth_login` - OAuth provider login (Google, Telegram)

### Account Management
- `password_change` - Password changed
- `email_change` - Email address changed
- `password_reset` - Password reset requested/completed
- `profile_update` - User profile updated

### Entity Operations
- `create` - Entity created (concept, dictionary, language)
- `update` - Entity updated
- `delete` - Entity deleted (soft or hard)
- `restore` - Soft-deleted entity restored

### Administrative Actions
- `role_change` - User role assigned/removed
- `ban_user` - User account banned
- `unban_user` - User account unbanned
- `bulk_assign_role` - Bulk role assignment
- `bulk_remove_role` - Bulk role removal

### File Operations
- `upload` - File uploaded
- `download` - File downloaded
- `delete_file` - File deleted

## Implementation

### Core Components

- `core/models/audit_log.py` - AuditLog model
- `core/services/audit_service.py` - Service with logging methods
- `core/schemas/audit.py` - GraphQL API

### Service Methods

```python
from core.services.audit_service import AuditService

audit_service = AuditService(db)

# Generic logging
audit_service.log(
    user_id=user.id,
    action="custom_action",
    description="Custom action description",
    status="success"
)

# Authentication logging
audit_service.log_login(user_id, ip_address, user_agent)
audit_service.log_logout(user_id, ip_address)
audit_service.log_register(user_id, method="email", ip_address)

# Entity CRUD logging
audit_service.log_entity_create(
    user_id=user.id,
    entity_type="concept",
    entity_id=concept.id,
    new_data={"name": concept.name},
    ip_address=request.client.host
)

audit_service.log_entity_update(
    user_id=user.id,
    entity_type="concept",
    entity_id=concept.id,
    old_data={"name": "Old Name"},
    new_data={"name": "New Name"}
)

audit_service.log_entity_delete(
    user_id=user.id,
    entity_type="concept",
    entity_id=concept.id,
    old_data={"name": concept.name}
)

# Retrieve logs
logs = audit_service.get_logs(
    user_id=user.id,
    action="login",
    limit=20,
    offset=0
)

# Get activity statistics
activity = audit_service.get_user_activity(
    user_id=user.id,
    days=30
)

# Cleanup old logs
audit_service.cleanup_old_logs(days=90)
```

## Database Schema

```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    old_data JSONB,
    new_data JSONB,
    description TEXT,
    status VARCHAR(20) DEFAULT 'success',
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_status ON audit_logs(status);
```

## Usage in Services

### Authentication Service

```python
# auth/services/auth_service.py
from core.services.audit_service import AuditService

class AuthService:
    def login(self, username: str, password: str, request):
        user = self._authenticate(username, password)

        # Log successful login
        audit_service = AuditService(self.db)
        audit_service.log_login(
            user_id=user.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )

        return self._create_tokens(user)
```

### Concept Service

```python
# languages/services/concept_service.py
from core.services.audit_service import AuditService

class ConceptService:
    def update_concept(self, concept_id: int, data: dict, user_id: int):
        concept = self._get_concept(concept_id)
        old_data = {"path": concept.path, "depth": concept.depth}

        # Update concept
        concept.path = data["path"]
        concept.depth = data["depth"]
        self.db.commit()

        # Log update
        audit_service = AuditService(self.db)
        audit_service.log_entity_update(
            user_id=user_id,
            entity_type="concept",
            entity_id=concept.id,
            old_data=old_data,
            new_data={"path": concept.path, "depth": concept.depth}
        )

        return concept
```

### Admin Service

```python
# auth/services/admin_service.py
from core.services.audit_service import AuditService

class AdminService:
    def ban_user(self, user_id: int, admin_id: int, reason: str):
        user = self._get_user(user_id)
        user.is_active = False
        self.db.commit()

        # Log ban action
        audit_service = AuditService(self.db)
        audit_service.log(
            user_id=admin_id,
            action="ban_user",
            entity_type="user",
            entity_id=user_id,
            description=f"User banned. Reason: {reason}",
            status="success"
        )

        return user
```

## Querying Audit Logs

### Get User's Recent Activity

```python
# Get last 20 actions by user
logs = audit_service.get_logs(
    user_id=42,
    limit=20,
    offset=0
)

for log in logs["logs"]:
    print(f"{log.created_at}: {log.action} - {log.description}")
```

### Get All Failed Login Attempts

```python
# Find failed logins in last 24 hours
from datetime import datetime, timedelta

failed_logins = audit_service.get_logs(
    action="login",
    status="failure",
    from_date=datetime.utcnow() - timedelta(days=1)
)
```

### Track Entity Changes

```python
# Get all changes to specific concept
concept_changes = audit_service.get_logs(
    entity_type="concept",
    entity_id=123
)

for change in concept_changes["logs"]:
    if change.action == "update":
        print(f"Changed from {change.old_data} to {change.new_data}")
```

### Get Activity Statistics

```python
# Get user activity for last 30 days
activity = audit_service.get_user_activity(
    user_id=42,
    days=30
)

for stat in activity:
    print(f"{stat['action']}: {stat['count']} times")

# Output:
# login: 45 times
# update: 23 times
# create: 12 times
```

## Security & Privacy

### Sensitive Data Filtering

Automatically filters sensitive fields before logging:

```python
SENSITIVE_FIELDS = [
    "password",
    "access_token",
    "refresh_token",
    "secret_key",
    "api_key"
]

def filter_sensitive_data(data: dict) -> dict:
    """Remove sensitive fields from data"""
    filtered = data.copy()
    for field in SENSITIVE_FIELDS:
        if field in filtered:
            filtered[field] = "***REDACTED***"
    return filtered
```

### Access Control

- **Users** can view their own audit logs
- **Admins** can view all audit logs
- **System** actions logged without user_id

### Data Retention

```python
# Automatically clean up logs older than 90 days
audit_service.cleanup_old_logs(days=90)

# Or configure via environment variable
AUDIT_LOG_RETENTION_DAYS=90
```

## Monitoring & Alerts

### Prometheus Metrics

```python
from core.metrics import audit_events_total

# Track audit events
audit_events_total.labels(
    action="login",
    status="success"
).inc()
```

### Alert Rules

```yaml
# Prometheus alert for suspicious activity
groups:
  - name: audit_alerts
    rules:
      - alert: MultipleFailedLogins
        expr: rate(audit_events_total{action="login",status="failure"}[5m]) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Multiple failed login attempts detected"

      - alert: MassDataDeletion
        expr: rate(audit_events_total{action="delete"}[5m]) > 10
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Mass data deletion detected"
```

## Analytics & Reporting

### Generate Activity Report

```python
def generate_activity_report(days=30):
    """Generate activity report for last N days"""
    from datetime import datetime, timedelta

    start_date = datetime.utcnow() - timedelta(days=days)

    # Get all logs in date range
    logs = audit_service.get_logs(
        from_date=start_date,
        limit=10000
    )

    # Group by action
    actions = {}
    for log in logs["logs"]:
        action = log.action
        actions[action] = actions.get(action, 0) + 1

    return {
        "period": f"Last {days} days",
        "total_events": logs["total"],
        "actions": actions,
        "most_active_users": get_most_active_users(logs["logs"])
    }
```

### Export Audit Logs

```python
def export_audit_logs(start_date, end_date, format="csv"):
    """Export audit logs to file"""
    logs = audit_service.get_logs(
        from_date=start_date,
        to_date=end_date,
        limit=100000
    )

    if format == "csv":
        return export_to_csv(logs["logs"])
    elif format == "json":
        return export_to_json(logs["logs"])
    elif format == "xlsx":
        return export_to_xlsx(logs["logs"])
```

## Best Practices

### What to Log

✅ **Do log:**
- Authentication events (login, logout, register)
- Authorization failures (access denied)
- Data modifications (create, update, delete)
- Administrative actions (role changes, user bans)
- Sensitive operations (password resets, email changes)
- System events (startup, shutdown, errors)

❌ **Don't log:**
- Passwords or other secrets
- Personal identifiable information (PII) unnecessarily
- High-frequency read operations (list, view)
- System health checks
- Static asset requests

### Log Granularity

```python
# BAD - Too generic
audit_service.log(user_id=42, action="update")

# GOOD - Specific and informative
audit_service.log_entity_update(
    user_id=42,
    entity_type="concept",
    entity_id=123,
    old_data={"name": "Old"},
    new_data={"name": "New"},
    description="Updated concept name from 'Old' to 'New'"
)
```

### Performance Considerations

```python
# Use async logging for high-throughput operations
from asyncio import create_task

async def async_log(action, user_id):
    create_task(audit_service.log(action=action, user_id=user_id))

# Batch logging for bulk operations
logs = []
for item in bulk_items:
    logs.append({
        "action": "create",
        "entity_id": item.id
    })
audit_service.bulk_log(logs)
```

## Troubleshooting

### Logs Growing Too Large

**Symptoms:**
- Database size increasing rapidly
- Slow query performance on audit_logs table

**Solutions:**
```python
# 1. Reduce retention period
audit_service.cleanup_old_logs(days=30)

# 2. Archive old logs to separate storage
archive_audit_logs(older_than_days=90)

# 3. Add partitioning
# See docs/DATABASE_PARTITIONING.md
```

### Missing Audit Logs

**Symptoms:**
- Actions not appearing in audit logs
- Gaps in audit trail

**Checks:**
1. Verify logging is enabled
2. Check if action is in logged actions list
3. Verify database connection
4. Check for exceptions in application logs

### Performance Impact

**Symptoms:**
- Requests taking longer after adding audit logging
- Database CPU usage increased

**Solutions:**
```python
# 1. Make logging asynchronous
async def log_async(action, user_id):
    await audit_service.log_async(action=action, user_id=user_id)

# 2. Use background queue (Celery)
@celery_task
def log_audit_event(action, user_id):
    audit_service.log(action=action, user_id=user_id)

# 3. Batch insert logs
audit_service.bulk_log(pending_logs)
```

## Related Documentation

- GraphQL API: [Query Documentation](../graphql/query/audit.md)
- [Admin Panel](admin_panel.md) - Admin audit trail
- [Security Best Practices](../SECURITY.md)
