# Development Guide

Complete guide for local development setup and workflow.

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd backend

# Copy environment configuration
cp .env.example .env

# Edit configuration
nano .env

# Start development environment
docker-compose -f docker-compose.dev.yml up
```

Application will be available at:
- **GraphQL Playground:** http://localhost:8000/graphql
- **Health Check:** http://localhost:8000/health
- **Detailed Health Check:** http://localhost:8000/health/detailed
- **Prometheus Metrics:** http://localhost:8000/metrics
- **MailPit UI:** http://localhost:8025

---

## Running the Application

### Docker (Recommended)

**Development mode** (with hot-reload and MailPit):
```bash
docker-compose -f docker-compose.dev.yml up
```

**Production mode:**
```bash
docker-compose up -d
```

**Stop services:**
```bash
docker-compose down
```

**View logs:**
```bash
docker-compose logs -f app
```

---

### Local Development (without Docker)

**Prerequisites:**
- Python 3.11+
- PostgreSQL 14+
- Redis 7+

**Setup:**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start application
python app.py
```

---

## Database Operations

### Migrations

**Create new migration:**
```bash
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback one migration:**
```bash
alembic downgrade -1
```

**View migration history:**
```bash
alembic history
```

**View current revision:**
```bash
alembic current
```

---

### Seeding Data

**Automatic seeding** (on startup if `SEED_DATABASE=true`):
The application automatically seeds test data on first run.

**Manual seeding:**
```bash
python scripts/seed_data.py
```

**Seeded data includes:**
- 8 languages (Russian, English, Spanish, French, German, Chinese, Japanese, Arabic)
- 5 roles (admin, moderator, editor, viewer, user)
- 5 test users with different roles
- ~80 concepts in hierarchical structure
- ~150 translations across multiple languages
- ~25,000 domain concepts about human body attractors (simplified version)

**Test accounts:**
- `admin / Admin123!` - Full access
- `moderator / Moderator123!` - User management
- `editor / Editor123!` - Content management
- `testuser / User123!` - Regular user

**Domain ontology seeding:**
The human body attractors ontology contains approximately 25,000 concepts organized in a hierarchical structure. 
By default, the simplified version is used (without min/max characteristics):

```bash
# Simplified version (default) - without characteristics
python scripts/seed_domain_concepts_simple.py

# Full version - with all characteristics
python scripts/seed_domain_concepts.py
```

---

## Testing

### Running Tests

**Run all tests:**
```bash
pytest
```

**Run with verbose output:**
```bash
pytest -v
```

**Run specific test file:**
```bash
pytest tests/test_app.py
```

**Run only unit tests** (fast):
```bash
pytest -m unit
```

**Run only integration tests** (requires Docker services):
```bash
pytest -m integration
```

**Run with coverage:**
```bash
pytest --cov=. --cov-report=html
```

View coverage report: `open htmlcov/index.html`

---

### Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── test_app.py           # Application tests
├── test_auth.py          # Authentication tests
├── test_admin.py         # Admin functionality tests
├── test_profile.py       # User profile tests
├── test_file_upload.py   # File upload tests
└── ...
```

**Test fixtures:**
- `db` - Database session
- `client` - Test client
- `test_user` - Regular user
- `admin_user` - Admin user
- `auth_headers` - Authorization headers

---

## Code Quality

### Pre-commit Hooks

**Install pre-commit:**
```bash
pip install pre-commit
pre-commit install
```

**Run all hooks:**
```bash
pre-commit run --all-files
```

**Hooks configured:**
- Black (code formatting)
- isort (import sorting)
- Flake8 (linting)
- mypy (type checking)
- Trailing whitespace removal
- YAML/JSON validation

---

### Manual Code Quality Checks

**Format code with Black** (100 char line length):
```bash
black . --line-length=100
```

**Sort imports:**
```bash
isort . --profile black --line-length 100
```

**Run linter:**
```bash
flake8 . --max-line-length=100 --extend-ignore=E203,W503
```

**Type checking:**
```bash
mypy . --ignore-missing-imports
```

---

## GraphQL Schema

### Export Schema

**Export to file:**
```bash
strawberry export-schema core.schemas.schema:schema > schema.graphql
```

**View schema in Playground:**
1. Open http://localhost:8000/graphql
2. Click "Docs" button on the right
3. Browse schema documentation

---

## Environment Configuration

### Required Variables

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

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (Development - MailPit)
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_USE_TLS=False
FROM_EMAIL=noreply@multipult.dev

# Application
DEBUG=True
SEED_DATABASE=true
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Optional Variables

```env
# Sentry (Error Tracking)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENABLE_TRACING=true
SENTRY_TRACES_SAMPLE_RATE=0.1

# OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
TELEGRAM_BOT_TOKEN=your-bot-token

# File Upload
UPLOAD_DIR=uploads

# Security Headers
SECURITY_HEADERS_ENABLED=true
CSP_POLICY=default-src 'self'
```

See `.env.example` for all available options.

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following [Architecture Guidelines](ARCHITECTURE.md)
- Follow [Code Patterns](PATTERNS.md)
- Add tests for new functionality

### 3. Run Tests

```bash
pytest
```

### 4. Check Code Quality

```bash
pre-commit run --all-files
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

**Commit message format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Build/tooling changes

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create Pull Request on GitHub.

---

## Debugging

### Docker Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f app
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Python Debugger

Add breakpoint in code:
```python
import pdb; pdb.set_trace()
```

Or use VS Code debugger with launch configuration:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": true
    }
  ]
}
```

### Database Inspection

```bash
# Connect to database
docker exec -it templates_postgres psql -U postgres -d multipult

# List tables
\dt

# Describe table
\d users

# Run query
SELECT * FROM users LIMIT 5;
```

### Redis Inspection

```bash
# Connect to Redis
docker exec -it templates_redis redis-cli

# List all keys
KEYS *

# Get value
GET verify:abc123

# Check TTL
TTL verify:abc123
```

---

## Common Issues

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Connection Failed

1. Check if PostgreSQL is running
2. Verify credentials in `.env`
3. Check network connectivity

### Module Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Migration Conflicts

```bash
# Rollback and reapply
alembic downgrade -1
alembic upgrade head
```

---

## Additional Resources

- **[Architecture Guide](ARCHITECTURE.md)** - System architecture
- **[Patterns & Conventions](PATTERNS.md)** - Code patterns
- **[GraphQL API](graphql/README.md)** - API documentation
- **[Features](features/README.md)** - Feature documentation
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment
