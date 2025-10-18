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
- Health Check: http://localhost:8000/health

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
- **Health checks**: `/health` endpoint checks database connectivity
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

---

Issue to solve: undefined
Your prepared branch: issue-1-1ae97023
Your prepared working directory: /tmp/gh-issue-solver-1760786079777
Your forked repository: konard/backend
Original repository (upstream): Godmy/backend

Proceed.