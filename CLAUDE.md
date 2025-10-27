# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

МультиПУЛЬТ is a modern Python backend with GraphQL API for managing templates, concepts, and multilingual content. Built with FastAPI/Starlette, Strawberry GraphQL, SQLAlchemy ORM, and PostgreSQL.

**Technology Stack:**
- Framework: FastAPI/Starlette
- GraphQL: Strawberry GraphQL
- ORM: SQLAlchemy
- Database: PostgreSQL 14+
- Cache: Redis 7+
- Testing: pytest

---

## Quick Start

```bash
# Development mode (with hot-reload and MailPit)
docker-compose -f docker-compose.dev.yml up

# Production mode
docker-compose up -d

# Run tests
pytest

# Run migrations
alembic upgrade head
```

Application available at:
- GraphQL Playground: http://localhost:8000/graphql
- Health Check: http://localhost:8000/health
- Detailed Health: http://localhost:8000/health/detailed
- Metrics: http://localhost:8000/metrics

---

## Documentation

### Core Documentation

- **[Development Guide](docs/DEVELOPMENT.md)** - Local setup, testing, debugging, code quality
- **[Architecture](docs/ARCHITECTURE.md)** - System architecture, data flow, modular structure
- **[Patterns & Conventions](docs/PATTERNS.md)** - Code patterns, best practices, adding modules
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment, SSL setup, monitoring

### API Documentation

- **[GraphQL API](docs/graphql/README.md)** - Complete API reference
  - [Queries](docs/graphql/query/README.md) - All GraphQL queries
  - [Mutations](docs/graphql/mutation/README.md) - All GraphQL mutations

### Features

Complete feature documentation available in **[docs/features/](docs/features/README.md)**:

**Health & Monitoring:**
- [Health Checks](docs/features/health_checks.md) - System health monitoring
- [Prometheus Metrics](docs/features/prometheus.md) - Application metrics
- [Database Pool Monitoring](docs/features/db_pool_monitoring.md) - Connection pool health
- [Request Tracing](docs/features/request_tracing.md) - Distributed tracing
- [Request Logging](docs/features/request_logging.md) - API logging
- [Structured Logging](docs/features/structured_logging.md) - JSON logging for ELK/CloudWatch
- [Audit Logging](docs/features/audit_logging.md) - Activity tracking
- [Sentry Error Tracking](docs/features/sentry.md) - Error monitoring

**Authentication & Users:**
- [Email Service](docs/features/email_service.md) - Email sending (MailPit/SMTP)
- [Email Verification](docs/features/email_verification.md) - Verification flows
- [User Profile Management](docs/features/user_profile.md) - Profile, password, email
- [Admin Panel](docs/features/admin_panel.md) - User management, statistics

**Content Management:**
- [File Upload System](docs/features/file_upload.md) - Secure uploads with thumbnails
- [Advanced Search](docs/features/search.md) - Full-text search with filters
- [Import/Export](docs/features/import_export.md) - Data import/export (JSON/CSV/XLSX)

**Data Management:**
- [Soft Delete](docs/features/soft_delete.md) - Soft delete with restore

**Security & Performance:**
- [Security Headers](docs/features/security_headers.md) - Security middleware
- [Rate Limiting](docs/features/rate_limiting.md) - API rate limiting per user/IP
- [HTTP Caching](docs/features/http_caching.md) - Cache-Control, ETag, 304 Not Modified
- [Redis Caching](docs/features/redis_caching.md) - Service-level caching with automatic invalidation
- [Graceful Shutdown](docs/features/graceful_shutdown.md) - Graceful shutdown handling

---

## Architecture Overview

МультиПУЛЬТ follows a **strict modular architecture**:

```
module_name/
├── models/          # SQLAlchemy models (database)
├── schemas/         # Strawberry GraphQL schemas (API)
└── services/        # Business logic (GraphQL-agnostic)
```

**Core modules:**
- `core/` - Base infrastructure, database, utilities
- `auth/` - Authentication, users, roles, permissions
- `languages/` - Languages, concepts, dictionaries

**Key principles:**
- **Models** - Database structure (SQLAlchemy ORM)
- **Services** - ALL business logic and validation
- **Schemas** - GraphQL API layer (orchestration only)

**See full architecture:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Development Workflow

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up

# Run tests
pytest -v

# Code quality checks
pre-commit run --all-files

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Format code
black . --line-length=100
isort . --profile black --line-length 100
```

**See detailed guide:** [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

---

## Key Patterns

### Adding New Modules

1. Create structure: `new_module/{models,schemas,services}/`
2. Define models (inherit from `BaseModel`)
3. Implement business logic in services
4. Create GraphQL schemas
5. Import models in `core/init_db.py`
6. Add schemas to `core/schemas/schema.py`

**See complete guide:** [docs/PATTERNS.md](docs/PATTERNS.md)

### Authentication

- JWT-based (access + refresh tokens)
- Access tokens: 30 minutes
- Refresh tokens: 7 days
- OAuth support: Google, Telegram

**Test accounts** (when `SEED_DATABASE=true`):
- `admin / Admin123!` - Full access
- `moderator / Moderator123!` - User management
- `editor / Editor123!` - Content management
- `testuser / User123!` - Regular user

---

## Environment Configuration

Key variables (see `.env.example`):

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=multipult
DB_USER=postgres
DB_PASSWORD=postgres

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT (CHANGE IN PRODUCTION!)
JWT_SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
SMTP_HOST=mailpit
SMTP_PORT=1025
FROM_EMAIL=noreply@multipult.dev

# Application
DEBUG=True
SEED_DATABASE=true
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## Testing

```bash
# All tests
pytest

# Specific test file
pytest tests/test_app.py

# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# With coverage
pytest --cov=. --cov-report=html
```

**See testing guide:** [docs/DEVELOPMENT.md#testing](docs/DEVELOPMENT.md#testing)

---

## Deployment

### Development
```bash
docker-compose -f docker-compose.dev.yml up
```

### Production (with Nginx)
```bash
# Configure environment
cp .env.production .env
nano .env

# Setup SSL
sudo certbot certonly --standalone -d yourdomain.com

# Run migrations
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

### Cloud Platforms (AWS/GCP/Azure)
Use cloud load balancers (no nginx needed).

**See complete guide:** [DEPLOYMENT.md](DEPLOYMENT.md)

**Production checklist:** [DEPLOYMENT.md#production-checklist](DEPLOYMENT.md#production-checklist)

---

## Important Notes

- **Migrations:** Use Alembic for all schema changes
- **Seed data:** Auto-populated on first run (8 languages, 5 roles, 5 users, ~80 concepts)
- **CORS:** Configured for localhost:5173 by default
- **Soft delete:** Core models support soft delete via `SoftDeleteMixin`
- **Concept hierarchy:** Uses materialized path pattern (`/root/parent/child/`)
- **Health checks:** Two endpoints - simple (`/health`) and detailed (`/health/detailed`)

---

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`):
1. PostgreSQL service container
2. Python 3.11 dependencies
3. pytest with test database
4. flake8 linting
5. Docker image build (on main branch)

---

## Support

- **Documentation:** See files above
- **GraphQL Playground:** http://localhost:8000/graphql
- **Metrics:** http://localhost:8000/metrics
- **MailPit UI:** http://localhost:8025 (dev only)

---

Issue to solve: undefined
Your prepared branch: issue-3-2d341cdb
Your prepared working directory: /tmp/gh-issue-solver-1761537615254
Your forked repository: konard/backend
Original repository (upstream): Godmy/backend

Proceed.