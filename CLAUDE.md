# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

МультиПУЛЬТ is a modern Python backend with GraphQL API for managing templates, concepts, and multilingual content. Built with FastAPI/Starlette, Strawberry GraphQL, SQLAlchemy ORM, and PostgreSQL.

## Development Commands

npm install -g @anthropic-ai/claude-code

### Running the Application

**Docker (Recommended):**
```bash
# Production mode
docker-compose up -d

# Development mode (with hot-reload)
docker-compose -f docker-compose.dev.yml up
```

**Local Development:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

Application will be available at:
- GraphQL Playground: http://localhost:8000/graphql
- Health Check (simple): http://localhost:8000/health
- Health Check (detailed): http://localhost:8000/health/detailed
- Prometheus Metrics: http://localhost:8000/metrics

### Testing

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_app.py

# Run only unit tests (fast)
pytest -m unit

# Run only integration tests (requires Docker services)
pytest -m integration

# Run with coverage (uncomment in pytest.ini)
pytest --cov=. --cov-report=html
```

### Health Checks

The application provides two health check endpoints for monitoring system status:

**Simple Health Check (Backward Compatible):**
```bash
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "database": "connected"
}
```

**Detailed Health Check (Comprehensive Monitoring):**
```bash
curl http://localhost:8000/health/detailed

# Response:
{
  "status": "healthy",
  "timestamp": 1737000000.123,
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12.34,
      "message": "Database connection successful"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 5.67,
      "message": "Redis connection successful"
    },
    "disk": {
      "status": "healthy",
      "percent_used": 45.2,
      "total_gb": 100.0,
      "used_gb": 45.2,
      "free_gb": 54.8,
      "message": "Disk usage at 45.2%"
    },
    "memory": {
      "status": "healthy",
      "percent_used": 65.5,
      "total_gb": 16.0,
      "used_gb": 10.5,
      "available_gb": 5.5,
      "message": "Memory usage at 65.5%"
    }
  }
}
```

**Status levels:**
- `healthy` - All components operating normally (HTTP 200)
- `degraded` - Some components have warnings but system is operational (HTTP 200)
- `unhealthy` - One or more critical components failed (HTTP 503)

**Monitoring thresholds:**
- Disk usage warning: 90%
- Memory usage warning: 90%

**Implementation:**
- `core/services/health_service.py` - HealthCheckService with component checks
- Uses `psutil` for system metrics (disk, memory)
- Measures response times for database and Redis

### Email Service

**MailPit** is used for email testing in development:

```bash
# Start services with MailPit
docker-compose -f docker-compose.dev.yml up

# Access MailPit web UI
open http://localhost:8025

# SMTP server listens on
localhost:1025
```

**Sending emails:**
```python
from core.email_service import email_service

# Send verification email
email_service.send_verification_email(
    to_email="user@example.com",
    username="john_doe",
    token="verification-token-123"
)

# Send password reset email
email_service.send_password_reset_email(
    to_email="user@example.com",
    username="john_doe",
    token="reset-token-456"
)

# Send custom email
email_service.send_email(
    to_email="user@example.com",
    subject="Custom Subject",
    html_content="<h1>HTML content</h1>",
    text_content="Plain text fallback"
)
```

**Email templates** are located in `templates/emails/` and use Jinja2.

### Email Verification & Password Reset

**Redis** is used for storing temporary tokens:

```bash
# Access Redis CLI
docker exec -it templates_redis redis-cli

# Check verification tokens
KEYS verify:*

# Check reset tokens
KEYS reset:*

# Check rate limits
KEYS rate:email:*
```

**GraphQL mutations:**
```graphql
# Register (automatically sends verification email)
mutation {
  register(input: {
    username: "user"
    email: "user@example.com"
    password: "SecurePass123!"
  }) {
    accessToken
    refreshToken
  }
}

# Verify email
mutation {
  verifyEmail(input: { token: "token_from_email" }) {
    success
    message
  }
}

# Request password reset
mutation {
  requestPasswordReset(input: { email: "user@example.com" }) {
    success
    message
  }
}

# Reset password
mutation {
  resetPassword(input: {
    token: "token_from_email"
    newPassword: "NewPass123!"
  }) {
    success
    message
  }
}
```

**Token TTLs:**
- Verification tokens: 24 hours
- Reset tokens: 1 hour
- Rate limiting: 3 requests/hour per email

**See full documentation:** [docs/EMAIL_VERIFICATION_FLOW.md](docs/EMAIL_VERIFICATION_FLOW.md)

---

### User Profile Management

Complete user profile management with password change, email change, and account deletion.

**Features:**
- Update profile fields (firstName, lastName, bio, language, timezone)
- Change password with current password verification
- Change email address with verification
- Soft delete account with password confirmation
- Field validation (bio max 500 chars, names max 50 chars)
- Email notifications for profile changes
- Redis-based token storage for email changes

**GraphQL mutations:**
```graphql
# Update profile
mutation UpdateProfile {
  updateProfile(
    firstName: "John"
    lastName: "Doe"
    bio: "Software engineer passionate about GraphQL"
    language: "en"
    timezone: "UTC"
  ) {
    id
    profile {
      firstName
      lastName
      bio
      language
      timezone
    }
  }
}

# Change password
mutation ChangePassword {
  changePassword(
    currentPassword: "OldPass123!"
    newPassword: "NewPass123!"
  ) {
    success
    message
  }
}

# Request email change (sends verification email)
mutation RequestEmailChange {
  requestEmailChange(
    newEmail: "newemail@example.com"
    currentPassword: "MyPass123!"
  ) {
    success
    message
  }
}

# Confirm email change (after clicking link in email)
mutation ConfirmEmailChange {
  confirmEmailChange(token: "token_from_email") {
    success
    message
  }
}

# Delete account (soft delete)
mutation DeleteAccount {
  deleteAccount(password: "MyPass123!") {
    success
    message
  }
}

# Query current user profile
query Me {
  me {
    id
    username
    email
    isVerified
    profile {
      firstName
      lastName
      bio
      avatar
      language
      timezone
    }
  }
}
```

**Profile fields:**
- `firstName` - First name (max 50 characters)
- `lastName` - Last name (max 50 characters)
- `bio` - Biography/description (max 500 characters)
- `avatar` - Avatar URL (managed via file upload system)
- `language` - Preferred language code (e.g., "en", "ru")
- `timezone` - Timezone string (e.g., "UTC", "Europe/Moscow")

**Security features:**
- Password verification required for sensitive operations
- Email change requires confirmation via email link
- Account deletion uses soft delete (can be restored by admin)
- All tokens stored in Redis with expiration
- Email change tokens valid for 24 hours

**Implementation:**
- `auth/services/profile_service.py` - ProfileService with all business logic
- `auth/schemas/user.py` - GraphQL mutations and queries
- `auth/models/profile.py` - UserProfileModel (one-to-one with User)
- `core/email_service.py` - Email templates for profile changes

**Validation rules:**
- First name: max 50 characters
- Last name: max 50 characters
- Bio: max 500 characters
- New password: min 8 characters
- Email: must be unique and valid format

---

### Admin Panel Features

Comprehensive admin panel with user management, system statistics, and bulk operations.

**Features:**
- User management (ban, unban, delete)
- Bulk role assignment/removal
- System statistics dashboard
- User filtering and search
- Audit logging for all admin actions
- Permission-based access control

**GraphQL Queries:**

**1. Get All Users (with filters):**
```graphql
query {
  allUsers(
    limit: 50
    offset: 0
    filters: {
      isActive: true
      isVerified: true
      roleName: "editor"
      search: "john"
    }
  ) {
    users {
      id
      username
      email
      isActive
      isVerified
      roles
      firstName
      lastName
      createdAt
    }
    total
    hasMore
  }
}
```

**2. Get System Statistics:**
```graphql
query {
  systemStats {
    users {
      total
      active
      verified
      newLast30Days
      banned
    }
    content {
      concepts
      dictionaries
      languages
    }
    files {
      total
      totalSizeMb
    }
    audit {
      totalLogs
      logsLast30Days
    }
    roles  # JSON object with role distribution
  }
}
```

**GraphQL Mutations:**

**1. Ban User:**
```graphql
mutation {
  banUser(userId: 123, reason: "Spam and abuse") {
    id
    username
    isActive  # false
  }
}
```

**2. Unban User:**
```graphql
mutation {
  unbanUser(userId: 123) {
    id
    username
    isActive  # true
  }
}
```

**3. Delete User Permanently:**
```graphql
mutation {
  deleteUserPermanently(userId: 123)  # Returns boolean
}
```
⚠️ **WARNING:** This is irreversible! Use soft delete (via user profile) instead.

**4. Bulk Assign Role:**
```graphql
mutation {
  bulkAssignRole(userIds: [10, 20, 30], roleName: "editor") {
    success
    count  # Number of users updated
    message
  }
}
```

**5. Bulk Remove Role:**
```graphql
mutation {
  bulkRemoveRole(userIds: [10, 20, 30], roleName: "editor") {
    success
    count
    message
  }
}
```

**Permission Requirements:**
- All admin queries require `admin:read:users` or `admin:read:system` permission
- All admin mutations require `admin:update:users` or `admin:delete:users` permission
- Only users with "admin" role have these permissions by default

**Audit Logging:**
All admin actions are automatically logged with:
- Admin user ID
- Action performed (ban_user, unban_user, bulk_assign_role, etc.)
- Target entity (user ID, role name)
- Timestamp
- IP address and User-Agent
- Success/failure status

**Safety Features:**
- Cannot ban/delete yourself
- Cannot delete users without admin permission
- All actions logged in audit trail
- Bulk operations skip invalid/not-found users
- Soft delete preferred over hard delete

**Implementation:**
- `auth/services/admin_service.py` - Business logic for all admin operations
- `auth/schemas/admin.py` - GraphQL API (queries and mutations)
- `core/schemas/schema.py` - Integration into main schema
- `tests/test_admin.py` - Comprehensive test suite

**Use Cases:**
- Ban abusive users
- Bulk promote users to moderators
- View system health dashboard
- Search and filter users
- Audit admin actions
- Manage user roles at scale

---

### File Upload System

The application supports secure file uploads with automatic thumbnail generation and validation.

**Features:**
- Secure file storage with sanitized filenames
- Automatic thumbnail generation (256x256) for images
- Size validation (5MB for avatars, 10MB for other files)
- MIME type validation (PNG, JPG, GIF, WEBP)
- Path traversal protection
- Integration with user profiles (avatars)

**Directory structure:**
```
uploads/
├── 20250116_abc123def456.png  # Original files
└── thumbnails/
    └── 20250116_abc123def456.png  # Auto-generated thumbnails
```

**GraphQL mutations:**
```graphql
# Upload avatar (automatically updates user profile)
mutation UploadAvatar($file: Upload!) {
  uploadAvatar(file: $file) {
    id
    filename
    url
    thumbnailUrl
    mimeType
    size
    sizeMb
    fileType
    width
    height
    createdAt
  }
}

# Upload generic file
mutation UploadFile($file: Upload!, $fileType: String!, $entityType: String, $entityId: Int) {
  uploadFile(
    file: $file
    fileType: $fileType
    entityType: $entityType
    entityId: $entityId
  ) {
    id
    filename
    url
    thumbnailUrl
    sizeMb
    createdAt
  }
}

# Get my files
query MyFiles {
  myFiles(fileType: "avatar", limit: 10) {
    id
    filename
    url
    thumbnailUrl
    sizeMb
    createdAt
  }
}

# Delete file
mutation DeleteFile($fileId: Int!) {
  deleteFile(fileId: $fileId)
}
```

**Implementation details:**
- `core/models/file.py` - File model with metadata
- `core/file_storage.py` - FileStorageService for filesystem operations
- `core/services/file_service.py` - Business logic and validation
- `core/schemas/file.py` - GraphQL API
- `app.py` - `/uploads/{filename:path}` endpoint for serving files

**Configuration:**
```env
# .env
UPLOAD_DIR=uploads
```

**See full testing guide:** [TESTING_GUIDE.md](TESTING_GUIDE.md)

### Error Tracking & Monitoring (Sentry)

Comprehensive error tracking and performance monitoring with Sentry integration.

**Features:**
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

**Setup:**

1. **Create Sentry project:**
   - Sign up at [sentry.io](https://sentry.io)
   - Create a new project (Python/Starlette)
   - Copy the DSN from project settings

2. **Configure environment variables:**
```bash
# .env
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENVIRONMENT=production
SENTRY_ENABLE_TRACING=true
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% in production
SENTRY_RELEASE=backend@1.0.0  # Optional, for release tracking
```

3. **Sentry automatically captures:**
   - Uncaught exceptions
   - Database errors
   - HTTP 500 errors
   - GraphQL errors

**Manual error capture:**
```python
from core.sentry import capture_exception, capture_message, add_breadcrumb

# Capture exception with context
try:
    process_payment(user_id=123, amount=100)
except Exception as e:
    event_id = capture_exception(e, user_id=123, operation="payment", amount=100)
    logger.error(f"Payment failed, Sentry event: {event_id}")

# Capture warning message
capture_message("User exceeded rate limit", level="warning", user_id=123)

# Add breadcrumb for tracking user actions
add_breadcrumb("User clicked checkout button", category="navigation", user_id=123)
```

**Performance monitoring:**
```python
from core.sentry import start_transaction

# Track performance of operations
with start_transaction("process_order", op="task") as transaction:
    transaction.set_tag("user_id", user.id)
    transaction.set_data("order_id", order.id)
    # Do work
    process_order(order)
```

**User context:**
User context is automatically set when a user is authenticated. You can also manually set it:
```python
from core.sentry import set_user_context, clear_user_context

# Set user context
set_user_context(user_id=123, username="john_doe", email="john@example.com")

# Clear on logout
clear_user_context()
```

**Sensitive data filtering:**
The following data is automatically filtered before sending to Sentry:
- Passwords
- JWT tokens
- API keys
- Authorization headers
- Cookies
- Any field containing "password", "token", "secret", etc.

**Implementation:**
- `core/sentry.py` - Sentry initialization and utilities
- `app.py` - Automatic initialization on startup
- Integrations: Starlette, SQLAlchemy, Logging
- Filter function: `before_send()` removes sensitive data

**Production recommendations:**
- Set `SENTRY_TRACES_SAMPLE_RATE=0.1` (10%) to reduce overhead
- Enable release tracking with `SENTRY_RELEASE`
- Configure alerts in Sentry UI for critical errors
- Set up Slack/email notifications
- Review error grouping and ignore non-critical errors

---

### Request ID & Distributed Tracing

Comprehensive request tracking system for tracing requests across the application, including HTTP handlers, GraphQL resolvers, database queries, and background tasks.

**Features:**
- Automatic request ID generation (UUID) for every HTTP request
- Request ID propagation through all application layers
- Context variables for thread-safe request tracking
- X-Request-ID header in all responses
- Automatic logging with request_id and user_id
- Support for background tasks and Celery
- Tracing helpers for manual instrumentation
- GraphQL context integration

**How it works:**
1. **RequestLoggingMiddleware** generates unique request_id for each request
2. Request ID stored in **context variables** (thread-safe)
3. All logs automatically include request_id and user_id
4. GraphQL context includes request_id for resolvers
5. Background tasks can propagate request_id

**Automatic logging format:**
```
[abc12345] [user:42] INFO - app - Processing request
[abc12345] [user:42] INFO - auth.services - User authenticated
[abc12345] [user:42] INFO - core.database - Query executed
```

**GraphQL integration:**
```python
# In any GraphQL resolver
@strawberry.field
def my_query(self, info) -> str:
    request_id = info.context["request_id"]
    logger.info(f"Processing query")  # Automatically includes request_id
    return "result"
```

**Manual request ID access:**
```python
from core.context import get_request_id, get_user_id

def my_function():
    request_id = get_request_id()  # Current request ID
    user_id = get_user_id()  # Current user ID (if authenticated)

    logger.info("Processing")  # Automatically includes both IDs
```

**Background tasks (async):**
```python
from core.tracing import with_request_context

@with_request_context
async def send_email_task(to_email: str):
    # request_id is automatically available in logs
    logger.info(f"Sending email to {to_email}")
```

**Celery tasks:**
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

**Manual tracing spans:**
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

**Client usage:**
All HTTP responses include `X-Request-ID` header for client-side tracking:
```bash
curl -v http://localhost:8000/health
# < X-Request-ID: abc12345
```

**Implementation:**
- `core/context.py` - Context variables and logging filter
- `core/tracing.py` - Tracing decorators and helpers
- `core/middleware/request_logging.py` - Middleware with request_id generation
- `app.py` - Logging configuration with RequestContextFilter
- `tests/test_request_tracing.py` - Comprehensive test suite

**Benefits:**
- **Debuggability** - Trace a single request through all logs
- **Observability** - Correlate errors across services
- **Performance** - Identify slow operations in request lifecycle
- **Security** - Audit user actions with request correlation
- **Production-ready** - Thread-safe, async-compatible, zero configuration

### Prometheus Metrics Collection

Comprehensive metrics collection for monitoring application performance, resource usage, and business logic.

**Features:**
- Automatic HTTP request tracking (count, duration, in-progress)
- System metrics (CPU, memory, file descriptors)
- Ready-to-use metrics for GraphQL, database, Redis
- Business logic metrics (registrations, emails, file uploads)
- Prometheus-compatible exposition format
- Path normalization for better grouping

**Access metrics:**
```bash
curl http://localhost:8000/metrics
```

**Available metrics:**

*HTTP Metrics (auto-collected):*
- `http_requests_total` - Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_in_progress` - Current in-flight requests

*System Metrics (auto-collected):*
- `process_cpu_usage_percent` - CPU usage
- `process_memory_bytes` - Memory consumption
- `process_open_fds` - Open file descriptors

*GraphQL Metrics (ready to use):*
- `graphql_query_duration_seconds` - Query execution time
- `graphql_query_errors_total` - Query errors by type

*Database Metrics (ready to use):*
- `db_connections_active` - Active database connections
- `db_query_duration_seconds` - Query execution time
- `db_errors_total` - Database errors

*Business Logic Metrics (ready to use):*
- `users_registered_total` - User registrations by method
- `emails_sent_total` - Emails sent by type and status
- `files_uploaded_total` - Files uploaded by type

**Usage in services:**
```python
from core.metrics import users_registered_total, emails_sent_total

# Track user registration
users_registered_total.labels(method='google').inc()

# Track email sending
emails_sent_total.labels(email_type='verification', status='success').inc()

# Track file upload
from core.metrics import files_uploaded_total
files_uploaded_total.labels(file_type='avatar').inc()
```

**Implementation:**
- `core/metrics.py` - All metrics definitions
- `core/middleware/metrics.py` - Automatic HTTP metrics collection
- `app.py` - Metrics endpoint registration
- `tests/test_metrics.py` - Comprehensive test suite

**Prometheus scrape configuration:**
```yaml
scrape_configs:
  - job_name: 'multipult-backend'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
```

**Grafana dashboard:**
Import metrics into Grafana for visualization and alerting. Key panels to create:
- Request rate (req/sec)
- Error rate (%)
- Latency percentiles (p50, p95, p99)
- Memory and CPU usage
- Database connection pool status

### Import/Export System

Comprehensive data import/export system supporting JSON, CSV, and XLSX formats.

**Features:**
- Export/import concepts, dictionaries, users, and languages
- Multiple formats: JSON, CSV, XLSX
- Filtering and validation
- Duplicate handling strategies (skip, update, fail)
- Validation-only mode (dry run)
- Automatic cleanup of old exports (24 hours)
- Job status tracking

**GraphQL mutations:**
```graphql
# Export data
mutation ExportConcepts {
  exportData(
    entityType: CONCEPTS
    format: JSON
    filters: { language: "en" }
  ) {
    jobId
    url
    expiresAt
    status
  }
}

# Import data
mutation ImportConcepts($file: Upload!) {
  importData(
    file: $file
    entityType: CONCEPTS
    options: {
      onDuplicate: UPDATE
      validateOnly: false
    }
  ) {
    jobId
    status
    message
  }
}

# Check job status
query ImportJobStatus {
  importJob(jobId: 123) {
    status
    totalCount
    processedCount
    errorCount
    errors
    progressPercent
  }
}
```

**Implementation:**
- `core/models/import_export_job.py` - Job tracking model
- `core/services/export_service.py` - Export logic (JSON, CSV, XLSX)
- `core/services/import_service.py` - Import logic with validation
- `core/schemas/import_export.py` - GraphQL API
- `app.py` - `/exports/{filename}` endpoint for downloading files

**See full documentation:** [docs/IMPORT_EXPORT.md](docs/IMPORT_EXPORT.md)

---

### Soft Delete System

Complete soft delete implementation with GraphQL API for managing deleted records.

**Features:**
- Soft delete mixin for all models (User, Concept, Dictionary, Language)
- Records marked as deleted instead of permanently removed
- Track who deleted the record and when
- Admin-only restore and permanent delete operations
- Query builders for active/deleted/all records
- Automatic filtering of deleted records in queries

**GraphQL API:**
```graphql
# Get list of deleted records (admin only)
query DeletedRecords {
  deletedRecords(entityType: CONCEPT, limit: 20, offset: 0) {
    entityType
    entityId
    deletedAt
    deletedByUsername
  }
}

# Restore a deleted record (admin only)
mutation RestoreRecord {
  restoreRecord(entityType: CONCEPT, entityId: 123)
}

# Permanently delete (admin only, irreversible!)
mutation PermanentDelete {
  permanentDelete(entityType: CONCEPT, entityId: 123)
}
```

**Available entity types:**
- `USER` - Users
- `CONCEPT` - Concepts
- `DICTIONARY` - Translations
- `LANGUAGE` - Languages

**Programmatic usage:**
```python
from auth.models.user import UserModel

# Soft delete
user.soft_delete(db, deleted_by_user_id=admin.id)

# Query only active
active_users = UserModel.active(db).all()

# Query deleted
deleted_users = UserModel.deleted(db).all()

# Query all (including deleted)
all_users = UserModel.with_deleted(db).all()

# Restore
user.restore(db)

# Check if deleted
if user.is_deleted():
    print("User is deleted")
```

**Implementation:**
- `core/models/mixins/soft_delete.py` - SoftDeleteMixin with all methods
- `core/schemas/soft_delete.py` - GraphQL queries and mutations
- Applied to: UserModel, ConceptModel, DictionaryModel, LanguageModel
- Indexed `deleted_at` column for fast queries
- Foreign key to `deleted_by` user

**Security:**
- Only admins can view deleted records
- Only admins can restore records
- Only admins can permanently delete
- Permanent delete requires record to be soft-deleted first

---

### API Request/Response Logging

Comprehensive logging of all API requests and responses for debugging and monitoring.

**Features:**
- Logs all HTTP requests (method, path, headers, body)
- Logs all responses (status, duration)
- Generates unique request ID for tracing
- Extracts user ID from JWT token
- Masks sensitive data (passwords, tokens, secrets)
- Configurable logging levels
- Request duration tracking
- X-Request-ID header in responses

**Example log output:**
```
INFO: [req-abc123] POST /graphql 200 (125ms) user_id=42
INFO: [req-abc123] GET /api/users 200 (15ms) user_id=42 body={"username": "john"}
WARNING: [req-def456] POST /auth/login 401 (89ms)
ERROR: [req-ghi789] GET /api/orders 500 (2341ms) user_id=42
```

**Configuration:**
```python
# app.py
app.add_middleware(
    RequestLoggingMiddleware,
    log_body=True,        # Log request/response bodies
    log_headers=False     # Log headers (can expose secrets!)
)
```

**Environment variables:**
```bash
# .env
REQUEST_LOGGING_ENABLED=true
REQUEST_LOGGING_BODY=true
REQUEST_LOGGING_HEADERS=false  # DON'T enable in production (leaks secrets)
REQUEST_LOGGING_LEVEL=INFO
```

**Features:**
- Automatic user ID extraction from JWT
- Sensitive data masking (password, token, secret, etc.)
- Unique request ID per request (for distributed tracing)
- Request duration in milliseconds
- Different log levels by status code:
  - 2xx → INFO
  - 4xx → WARNING
  - 5xx → ERROR

**Implementation:**
- `core/middleware/request_logging.py` - RequestLoggingMiddleware
- `app.py` - Automatically enabled
- Masks fields: password, token, secret, authorization, api_key, access_token, refresh_token

**Use cases:**
- Debugging customer issues
- API usage analytics
- Security auditing
- Performance monitoring
- Distributed tracing (via X-Request-ID)

---

### Database Connection Pool Monitoring

Prometheus metrics for monitoring SQLAlchemy connection pool health and usage.

**Features:**
- Real-time connection pool statistics
- Prometheus-compatible metrics
- Automatic updates on /metrics endpoint scrape
- No performance impact (reads existing pool state)
- Alerts for pool exhaustion

**Available metrics:**
- `db_pool_size` - Total connection pool size
- `db_pool_checked_out` - Active connections (in use)
- `db_pool_checked_in` - Available connections (idle)
- `db_pool_overflow` - Current overflow connections
- `db_pool_num_overflow` - Maximum overflow connections allowed

**Prometheus query examples:**
```promql
# Connection pool usage percentage
(db_pool_checked_out / db_pool_size) * 100

# Available connections
db_pool_checked_in

# Pool exhaustion alert (over 90% usage)
(db_pool_checked_out / db_pool_size) > 0.9
```

**Implementation:**
- `core/metrics.py` - Prometheus metrics and `update_db_pool_metrics()` function
- `app.py` - Automatic update on /metrics endpoint
- Metrics updated on every Prometheus scrape (typically every 15s)

**Grafana dashboard panels:**
1. Connection Pool Usage (%) - Gauge
2. Active vs Available Connections - Time series
3. Overflow Connections - Counter
4. Pool Exhaustion Events - Alert

**Database configuration:**
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

**Monitoring best practices:**
- Alert when pool usage > 90%
- Alert when overflow connections > 0 for extended period
- Track connection acquisition time
- Monitor for connection leaks (checked_out never decreasing)

---

### Security Headers Middleware

Automatic security headers added to all HTTP responses to protect against common web vulnerabilities.

**Features:**
- X-Content-Type-Options: nosniff (prevents MIME type sniffing)
- X-Frame-Options: DENY (prevents clickjacking)
- X-XSS-Protection: 1; mode=block (enables XSS filter)
- Strict-Transport-Security (HSTS): Enforces HTTPS in production
- Content-Security-Policy: Restricts resource loading
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: Restricts dangerous browser features
- Configurable via environment variables
- Can be disabled for development

**Configuration:**
```bash
# .env
SECURITY_HEADERS_ENABLED=true  # Enable/disable (default: true)
CSP_POLICY=default-src 'self'; script-src 'self' 'unsafe-inline'
HSTS_MAX_AGE=31536000  # 1 year in seconds
FRAME_OPTIONS=DENY  # or SAMEORIGIN
ENVIRONMENT=production  # HSTS only enabled in production
```

**Implementation:**
- `core/middleware/security_headers.py` - SecurityHeadersMiddleware
- `app.py` - Automatically added to all requests
- `tests/test_security_headers.py` - Comprehensive test suite

**Testing:**
```bash
# Check headers in response
curl -I http://localhost:8000/health

# Expected headers:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Content-Security-Policy: default-src 'self'...
# Referrer-Policy: strict-origin-when-cross-origin
# Permissions-Policy: geolocation=(), microphone=()...
```

---

### Graceful Shutdown Handling

Ensures the application shuts down gracefully without interrupting active requests.

**Features:**
- Signal handlers for SIGTERM (Docker, K8s) and SIGINT (Ctrl+C)
- Waits for active requests to complete (configurable timeout)
- Rejects new requests during shutdown (returns 503)
- Closes database connections gracefully
- Closes Redis connections
- Flushes logs
- Health checks return 503 during shutdown
- Cross-platform support (Unix and Windows)

**Configuration:**
```bash
# .env
SHUTDOWN_TIMEOUT=30  # Maximum seconds to wait for requests (default: 30)
```

**Implementation:**
- `core/shutdown.py` - GracefulShutdown handler with signal management
- `core/middleware/shutdown.py` - ShutdownMiddleware (rejects requests during shutdown)
- `app.py` - Automatically configured on startup

**How it works:**
1. Application receives SIGTERM/SIGINT signal
2. Shutdown handler sets `is_shutting_down` flag
3. New requests are rejected with 503 status
4. Active requests complete (up to `SHUTDOWN_TIMEOUT` seconds)
5. Custom shutdown callbacks run (if configured)
6. Database connections closed
7. Redis connections closed
8. Logs flushed
9. Application exits cleanly

**Testing shutdown:**
```bash
# Start application
python app.py

# Send SIGTERM signal (in another terminal)
kill -TERM <pid>

# Or press Ctrl+C

# Check logs:
# INFO: Received SIGTERM signal, initiating graceful shutdown...
# INFO: Rejecting new requests...
# INFO: Waiting up to 30s for active requests to complete...
# INFO: Closing database connections...
# INFO: Database connections closed
# INFO: Closing Redis connections...
# INFO: Redis connections closed
# INFO: Flushing logs...
# INFO: Graceful shutdown completed successfully
```

**Production deployment:**
- Docker/Kubernetes automatically send SIGTERM on shutdown
- Configure probes to check `/health` endpoint
- Set `terminationGracePeriodSeconds` >= `SHUTDOWN_TIMEOUT` in K8s
- Uvicorn configured with `timeout_graceful_shutdown` parameter

---

### Advanced Search & Filtering

Powerful full-text search functionality for concepts and translations with filtering, sorting, and pagination.

**Features:**
- PostgreSQL full-text search (case-insensitive)
- Multi-language search across translations
- Filtering by language, category path, date range
- Multiple sort options (relevance, alphabetical, date)
- Pagination with total count and "has_more" indicator
- Autocomplete/suggestions for search input
- Popular concepts query
- N+1 query prevention with eager loading

**GraphQL queries:**
```graphql
# Full-text search with all filters
query SearchConcepts {
  searchConcepts(
    filters: {
      query: "пользователь"
      languageIds: [1, 2]  # Russian and English
      categoryPath: "/users/"
      fromDate: "2024-01-01T00:00:00"
      toDate: "2025-01-31T23:59:59"
      sortBy: RELEVANCE
      limit: 20
      offset: 0
    }
  ) {
    results {
      concept {
        id
        path
        depth
      }
      dictionaries {
        id
        name
        description
        languageId
      }
      relevanceScore
    }
    total
    hasMore
    limit
    offset
  }
}

# Search suggestions/autocomplete
query SearchSuggestions {
  searchSuggestions(query: "user", languageId: 1, limit: 5)
}

# Get popular concepts
query PopularConcepts {
  popularConcepts(limit: 10) {
    concept { id path }
    dictionaries {
      name
      description
    }
    relevanceScore
  }
}
```

**Sort options:**
- `RELEVANCE` - Best match first (by depth and query match)
- `ALPHABET` - Alphabetical by concept path
- `DATE` - Newest concepts first

**Implementation:**
- `languages/services/search_service.py` - SearchService with all search logic
- `languages/schemas/search.py` - GraphQL schema with 3 queries
- Uses PostgreSQL `ILIKE` for case-insensitive search
- `joinedload` for eager loading to prevent N+1 queries
- Soft-delete aware (only searches active records)

**Performance tips:**
- Language filters converted to IDs for efficient DB queries
- Results limited to max 100 per page
- Suggestions limited to max 20
- Indexed columns: `concept.path`, `dictionary.language_id`, `dictionary.concept_id`

**Example frontend usage:**
```typescript
// Search with debouncing
const searchConcepts = async (query: string, languageIds: number[]) => {
  const result = await graphqlClient.query({
    query: SEARCH_CONCEPTS_QUERY,
    variables: {
      filters: {
        query,
        languageIds,
        limit: 20,
        offset: 0,
        sortBy: 'RELEVANCE'
      }
    }
  });
  return result.data.searchConcepts;
};

// Autocomplete with debouncing
const getSuggestions = async (query: string) => {
  const result = await graphqlClient.query({
    query: SEARCH_SUGGESTIONS_QUERY,
    variables: { query, limit: 5 }
  });
  return result.data.searchSuggestions;
};
```

---

### Audit Logging System

Comprehensive audit logging system for tracking all important user actions and system events.

**Features:**
- Automatic logging of authentication events (login, logout, register, OAuth)
- Entity CRUD operation tracking
- IP address and User-Agent capture
- Before/after data snapshots (JSON)
- Admin and user-level queries
- Activity statistics
- Automatic cleanup of old logs

**GraphQL queries:**
```graphql
# View my audit logs
query MyAuditLogs {
  myAuditLogs(action: "login", limit: 10) {
    logs {
      id
      action
      entityType
      entityId
      description
      status
      ipAddress
      createdAt
    }
    total
    hasMore
  }
}

# View all audit logs (admin only)
query AuditLogs {
  auditLogs(
    filters: {
      userId: 123
      action: "login"
      entityType: "concept"
      status: "success"
      fromDate: "2025-01-01T00:00:00"
      toDate: "2025-12-31T23:59:59"
    }
    limit: 100
    offset: 0
  ) {
    logs {
      id
      userId
      action
      entityType
      entityId
      oldData
      newData
      description
      status
      createdAt
    }
    total
    hasMore
  }
}

# Get user activity statistics
query UserActivity {
  userActivity(userId: 123, days: 30) {
    action
    count
  }
}
```

**Implementation details:**
- `core/models/audit_log.py` - AuditLog model
- `core/services/audit_service.py` - Service with logging methods:
  - `log()` - Generic logging
  - `log_login()`, `log_logout()`, `log_register()` - Auth events
  - `log_entity_create()`, `log_entity_update()`, `log_entity_delete()` - CRUD tracking
  - `get_logs()` - Retrieve with filters
  - `get_user_activity()` - Statistics
  - `cleanup_old_logs()` - Automatic cleanup
- `core/schemas/audit.py` - GraphQL API

**Usage in services:**
```python
from core.services.audit_service import AuditService

# In your service/mutation
audit_service = AuditService(db)

# Log entity creation
audit_service.log_entity_create(
    user_id=user.id,
    entity_type="concept",
    entity_id=concept.id,
    new_data={"name": concept.name, "description": concept.description},
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)

# Log entity update
audit_service.log_entity_update(
    user_id=user.id,
    entity_type="concept",
    entity_id=concept.id,
    old_data={"name": "Old Name"},
    new_data={"name": "New Name"},
    ip_address=request.client.host
)
```

**Logged actions:**
- `login`, `logout`, `register`, `oauth_login`
- `password_change`, `email_change`, `password_reset`
- `create`, `update`, `delete` (for any entity)
- `upload` (file uploads)
- `profile_update`, `role_change`

### Database Operations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Seed database manually (also runs automatically on startup if SEED_DATABASE=true)
python scripts/seed_data.py
```

### Code Quality

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Format code with black (100 char line length)
black . --line-length=100

# Sort imports
isort . --profile black --line-length 100

# Run linter
flake8 . --max-line-length=100 --extend-ignore=E203,W503

# Type checking
mypy . --ignore-missing-imports
```

### GraphQL Schema Export

```bash
strawberry export-schema core.schemas.schema:schema > schema.graphql
```

## Architecture

### Modular Structure

The project follows a **strict modular architecture** where each module is self-contained:

```
module_name/
├── models/          # SQLAlchemy models (database structure)
├── schemas/         # Strawberry GraphQL schemas (API layer)
└── services/        # Business logic (independent of GraphQL)
```

**Core modules:**
- `core/` - Base infrastructure (database, init, base models)
- `auth/` - Authentication, users, roles, permissions, profiles
- `languages/` - Languages, concepts (hierarchical), dictionaries (translations)

### Separation of Concerns

1. **Models** - SQLAlchemy ORM models defining database tables and relationships. Inherit from `core.models.base.BaseModel` which provides `id`, `created_at`, `updated_at`.

2. **Services** - Contains ALL business logic, validation, and database operations. Services are GraphQL-agnostic and can be reused anywhere.

3. **Schemas** - Strawberry GraphQL types, queries, and mutations. They orchestrate service calls, handle GraphQL-specific concerns, and transform data to GraphQL types.

### Data Flow

```
GraphQL Request
    ↓
Schemas (validation, parsing)
    ↓
Services (business logic, DB operations)
    ↓
Models (database interaction)
    ↓
Services (formatting response)
    ↓
Schemas (return GraphQL response)
```

### Schema Integration

All module schemas are unified in `core/schemas/schema.py`:

```python
@strawberry.type
class Query(
    LanguageQuery,
    ConceptQuery,
    DictionaryQuery,
    UserQuery,
    RoleQuery,
    FileQuery,
    AuditLogQuery
):
    pass

@strawberry.type
class Mutation(
    LanguageMutation,
    ConceptMutation,
    DictionaryMutation,
    UserMutation,
    AuthMutation,
    RoleMutation,
    FileMutation
):
    pass

schema = strawberry.Schema(Query, Mutation)
```

### Database Models & Relationships

**Core relationships:**
- `User` → `Role` → `Permission` (many-to-many through join tables)
- `User` → `Profile` (one-to-one)
- `User` → `File` (one-to-many, uploaded files)
- `User` → `AuditLog` (one-to-many, activity logs)
- `Profile` → `File` (avatar_file_id foreign key)
- `Language` ← `Dictionary` → `Concept` (translations link language to concepts)
- `Concept` is hierarchical (self-referential with `parent_id`, uses `path` field for queries)

## Key Patterns & Conventions

### Adding New Modules

1. Create module structure: `new_module/{models,schemas,services}/`
2. Define SQLAlchemy models in `models/`, inherit from `BaseModel`
3. Implement business logic in `services/`
4. Create GraphQL schemas in `schemas/`
5. Import models in `core/init_db.py` → `import_all_models()`
6. Add schema classes to `core/schemas/schema.py`

### Database Initialization

On startup, `app.py` calls `init_database()` which:
1. Waits for PostgreSQL connection (with retries)
2. Imports all models from all modules
3. Creates tables via `Base.metadata.create_all()`
4. Optionally seeds test data if `SEED_DATABASE=true`

The seeding script is **idempotent** - it checks for existing data and skips creation to avoid duplicates.

### Authentication

- JWT-based authentication with access & refresh tokens
- Access tokens expire in 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Refresh tokens expire in 7 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
- Passwords hashed with bcrypt
- Use `auth/dependencies/` for GraphQL field-level authorization checks

**Test accounts** (available when `SEED_DATABASE=true`):
- `admin / Admin123!` - Full access
- `moderator / Moderator123!` - User management
- `editor / Editor123!` - Content management
- `testuser / User123!` - Regular user

### Environment Configuration

Key environment variables (see `.env.example`):
- `JWT_SECRET_KEY` - **MUST change in production**
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - Database connection
- `SEED_DATABASE` - Set to `false` in production to disable test data seeding
- `ALLOWED_ORIGINS` - CORS configuration (comma-separated)
- `DEBUG` - Set to `False` in production

**Email configuration:**
- `SMTP_HOST` - SMTP server hostname (default: `mailpit` for dev, use SendGrid/AWS SES for prod)
- `SMTP_PORT` - SMTP port (default: `1025` for dev, `587` for prod with TLS)
- `SMTP_USERNAME` - SMTP authentication username (empty for MailPit)
- `SMTP_PASSWORD` - SMTP authentication password (empty for MailPit)
- `SMTP_USE_TLS` - Enable TLS encryption (`False` for dev, `True` for prod)
- `FROM_EMAIL` - Sender email address (default: `noreply@multipult.dev`)
- `FRONTEND_URL` - Frontend URL for email links (default: `http://localhost:5173`)

**File upload configuration:**
- `UPLOAD_DIR` - Directory for storing uploaded files (default: `uploads`)

## Code Style

- **PEP 8** compliance
- **100 character line limit** (enforced by black/flake8)
- **Type hints** preferred for function signatures
- **Docstrings** for public functions and classes
- Use **async/await** for I/O operations where beneficial
- Pre-commit hooks enforce: black, isort, flake8, mypy, trailing whitespace, YAML/JSON validation

## Testing Strategy

- Tests live in `tests/` directory
- Use pytest with async support (`pytest-asyncio`)
- Configure via `pytest.ini`
- Test services independently (unit tests) and API endpoints (integration tests)
- Use `conftest.py` for shared fixtures (DB session, test client, etc.)

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on push/PR to main/develop:
1. Sets up PostgreSQL service container
2. Installs Python 3.11 dependencies
3. Runs pytest with test database
4. Runs flake8 linting (two passes: critical errors, then full analysis)
5. Builds Docker image on successful main branch pushes

## Important Notes

- **Database migrations**: Use Alembic for schema changes, never modify database directly
- **Seed data**: Automatically populated on first run (8 languages, 5 roles, 5 test users, ~80 concepts, ~150 translations)
- **CORS**: Configured in `app.py` for frontend origins (localhost:5173 by default)
- **Health checks**: Two endpoints available:
  - `/health` - Simple database connectivity check (backward compatible)
  - `/health/detailed` - Comprehensive system monitoring (database, Redis, disk, memory)
- **Soft delete**: Core models (User, Concept, Dictionary, Language) support soft delete via `SoftDeleteMixin`
- **Concept hierarchy**: Uses materialized path pattern (stored in `path` field like `/root/parent/child/`)
- **Error handling**: Services should raise exceptions, schemas should catch and return appropriate GraphQL errors

## OAuth Authentication

The application supports OAuth authentication via **Google** and **Telegram**.

### Setup OAuth Providers

**Google OAuth:**
1. Create project in [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID
3. Add authorized redirect URIs
4. Copy Client ID and Client Secret to `.env`:
   ```env
   GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_client_secret
   ```

**Telegram OAuth:**
1. Create bot via [@BotFather](https://t.me/BotFather) with `/newbot`
2. Set domain with `/setdomain` command
3. Copy bot token to `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ```

### GraphQL Mutations

```graphql
# Login with Google
mutation {
  loginWithGoogle(input: {
    idToken: "google_id_token_from_frontend"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}

# Login with Telegram
mutation {
  loginWithTelegram(input: {
    id: "123456789"
    authDate: "1640000000"
    hash: "telegram_hmac_hash"
    firstName: "John"
    username: "johndoe"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

### How OAuth Works

1. Frontend requests OAuth provider authentication
2. Provider returns token/auth data to frontend
3. Frontend sends token to backend via GraphQL mutation
4. **Backend verifies token with provider** (important for security!)
5. Backend creates/links user account
6. Backend returns JWT tokens for API access

**OAuth users:**
- Automatically marked as verified (`is_verified: true`)
- Created with random password (not used for OAuth login)
- Linked by email (Google) or stored in `oauth_connections` table
- Can link multiple OAuth providers to same account

**See full documentation:** [docs/OAUTH_SETUP.md](docs/OAUTH_SETUP.md)

## Deployment

### Development Environment

```bash
# Use docker-compose.dev.yml (includes MailPit, hot-reload)
docker-compose -f docker-compose.dev.yml up
```

No nginx needed for development - Uvicorn handles everything.

### Production Deployment

**Two options:**

#### Option 1: VPS/Dedicated Server with Nginx (Recommended)

Use `docker-compose.prod.yml` which includes:
- Nginx (reverse proxy, SSL, rate limiting, compression)
- Application (4 Uvicorn workers)
- PostgreSQL (production settings)
- Redis (with password, persistence)

**Why nginx?**
- SSL/TLS termination
- Rate limiting (10 req/s for GraphQL, configurable)
- Compression (gzip)
- Security headers
- Load balancing across workers
- Protection from slow clients

**Setup:**
```bash
# 1. Configure environment
cp .env.production .env
nano .env  # Update all values

# 2. Setup SSL (Let's Encrypt)
sudo certbot certonly --standalone -d yourdomain.com

# 3. Update nginx.conf with your domain
nano nginx/nginx.conf

# 4. Run migrations
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# 5. Start services
docker-compose -f docker-compose.prod.yml up -d
```

#### Option 2: Cloud Platform (AWS/GCP/Azure)

**DON'T use nginx** - cloud load balancers handle everything.

Use `docker-compose.simple.yml` or deploy directly to:
- AWS ECS/Fargate with ALB
- Google Cloud Run with Cloud Load Balancer
- Azure App Service with Application Gateway

Cloud handles:
- SSL/TLS (automatic with Let's Encrypt or managed certs)
- Load balancing
- Auto-scaling
- Health checks
- Rate limiting (via WAF)

**See full deployment guide:** [DEPLOYMENT.md](DEPLOYMENT.md)

### When to Use Nginx

| Use Case | Use Nginx? |
|----------|-----------|
| VPS/Dedicated Server | ✅ YES |
| AWS/GCP/Azure with Load Balancer | ❌ NO |
| Simple/Small Project | 🤷 Optional |
| Multiple Uvicorn Workers | ✅ YES |
| Need Advanced Rate Limiting | ✅ YES |
| Need Custom Caching Rules | ✅ YES |

### Production Checklist

Before deploying to production:

- [ ] Change `JWT_SECRET_KEY` to random value (`openssl rand -hex 32`)
- [ ] Set strong `DB_PASSWORD` and `REDIS_PASSWORD`
- [ ] Set `SEED_DATABASE=false`
- [ ] Set `DEBUG=False`
- [ ] Configure production SMTP (SendGrid/AWS SES, not MailPit)
- [ ] Update `ALLOWED_ORIGINS` to production domain(s)
- [ ] Setup SSL certificate (Let's Encrypt recommended)
- [ ] Configure OAuth credentials for production
- [ ] Run database migrations
- [ ] Setup backups (database + Redis)
- [ ] Configure monitoring (logs, health checks, alerts)
- [ ] **Configure Sentry error tracking:**
  - [ ] Create Sentry project at sentry.io
  - [ ] Set `SENTRY_DSN` in production environment
  - [ ] Set `ENVIRONMENT=production`
  - [ ] Set `SENTRY_TRACES_SAMPLE_RATE=0.1` (10%)
  - [ ] Configure `SENTRY_RELEASE` for deploy tracking
  - [ ] Setup alerts and notifications in Sentry UI
- [ ] **Configure Prometheus metrics monitoring:**
  - [ ] Setup Prometheus server to scrape `/metrics` endpoint
  - [ ] Configure scrape interval (15s recommended)
  - [ ] Setup Grafana for visualization
  - [ ] Create dashboards for key metrics
  - [ ] Configure alerts for critical thresholds (error rate, latency, memory)
- [ ] Test OAuth flows in production
- [ ] Setup SSL auto-renewal (cron job for certbot)

### Nginx Configuration

Production nginx config (`nginx/nginx.conf`) includes:
- HTTPS with TLSv1.2/1.3
- Rate limiting: 10 req/s for GraphQL (burst 20)
- Security headers (X-Frame-Options, HSTS, CSP)
- Gzip compression
- HTTP to HTTPS redirect
- Custom error pages

Development nginx config (`nginx/nginx.dev.conf`):
- HTTP only (no SSL)
- Relaxed rate limits (100 req/s)
- CORS enabled for all origins

**Test nginx config:**
```bash
docker run --rm -v $(pwd)/nginx/nginx.conf:/etc/nginx/nginx.conf:ro nginx nginx -t
```

**Reload nginx after changes:**
```bash
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```
