# Development Patterns & Conventions

Comprehensive guide to development patterns, conventions, and best practices for this project.

## Table of Contents

- [Module Architecture](#module-architecture)
- [Adding New Modules](#adding-new-modules)
- [Database Patterns](#database-patterns)
- [Authentication & Security](#authentication--security)
- [Environment Configuration](#environment-configuration)
- [Code Style](#code-style)
- [Testing Strategy](#testing-strategy)
- [CI/CD Pipeline](#cicd-pipeline)
- [Best Practices](#best-practices)

---

## Module Architecture

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

---

## Adding New Modules

### Step-by-Step Guide

Follow these steps when creating a new module:

#### 1. Create Module Structure

```bash
mkdir -p new_module/{models,schemas,services}
touch new_module/__init__.py
touch new_module/models/__init__.py
touch new_module/schemas/__init__.py
touch new_module/services/__init__.py
```

#### 2. Define SQLAlchemy Models

Create `new_module/models/your_model.py`:

```python
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from core.models.base import BaseModel

class YourModel(BaseModel):
    __tablename__ = "your_table"

    # Columns
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="your_models")

    def __repr__(self):
        return f"<YourModel(id={self.id}, name={self.name})>"
```

**Best practices:**
- Always inherit from `BaseModel` (provides `id`, `created_at`, `updated_at`)
- Use descriptive table names (lowercase, plural)
- Add indexes for frequently queried columns
- Define relationships with `back_populates`
- Add `__repr__` for debugging

#### 3. Implement Business Logic in Services

Create `new_module/services/your_service.py`:

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from new_module.models.your_model import YourModel

class YourService:
    """Service for managing your resources."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, description: str, user_id: int) -> YourModel:
        """Create a new resource."""
        instance = YourModel(
            name=name,
            description=description,
            user_id=user_id
        )
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def get_by_id(self, id: int) -> Optional[YourModel]:
        """Get resource by ID."""
        return self.db.query(YourModel).filter(YourModel.id == id).first()

    def list_by_user(self, user_id: int, limit: int = 20, offset: int = 0) -> List[YourModel]:
        """List resources for a user."""
        return (
            self.db.query(YourModel)
            .filter(YourModel.user_id == user_id)
            .limit(limit)
            .offset(offset)
            .all()
        )

    def update(self, id: int, name: Optional[str] = None, description: Optional[str] = None) -> Optional[YourModel]:
        """Update resource."""
        instance = self.get_by_id(id)
        if not instance:
            return None

        if name is not None:
            instance.name = name
        if description is not None:
            instance.description = description

        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, id: int) -> bool:
        """Delete resource."""
        instance = self.get_by_id(id)
        if not instance:
            return False

        self.db.delete(instance)
        self.db.commit()
        return True
```

**Best practices:**
- Services should be GraphQL-agnostic
- Accept database session in constructor
- Return domain models, not GraphQL types
- Raise exceptions for business logic errors
- Use type hints for clarity
- Add docstrings for public methods

#### 4. Create GraphQL Schemas

Create `new_module/schemas/your_schema.py`:

```python
import strawberry
from typing import List, Optional
from strawberry.types import Info
from new_module.models.your_model import YourModel
from new_module.services.your_service import YourService

@strawberry.type
class YourType:
    """GraphQL type for your resource."""
    id: int
    name: str
    description: Optional[str]
    created_at: str
    updated_at: str

    @staticmethod
    def from_model(model: YourModel) -> "YourType":
        """Convert SQLAlchemy model to GraphQL type."""
        return YourType(
            id=model.id,
            name=model.name,
            description=model.description,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat(),
        )

@strawberry.input
class CreateYourInput:
    """Input for creating resource."""
    name: str
    description: Optional[str] = None

@strawberry.input
class UpdateYourInput:
    """Input for updating resource."""
    id: int
    name: Optional[str] = None
    description: Optional[str] = None

@strawberry.type
class YourQuery:
    """GraphQL queries for your resource."""

    @strawberry.field
    def your_resource(self, info: Info, id: int) -> Optional[YourType]:
        """Get resource by ID."""
        db = info.context["db"]
        service = YourService(db)
        model = service.get_by_id(id)
        return YourType.from_model(model) if model else None

    @strawberry.field
    def my_resources(self, info: Info, limit: int = 20, offset: int = 0) -> List[YourType]:
        """Get my resources."""
        db = info.context["db"]
        user = info.context["user"]
        if not user:
            raise Exception("Authentication required")

        service = YourService(db)
        models = service.list_by_user(user.id, limit, offset)
        return [YourType.from_model(model) for model in models]

@strawberry.type
class YourMutation:
    """GraphQL mutations for your resource."""

    @strawberry.mutation
    def create_resource(self, info: Info, input: CreateYourInput) -> YourType:
        """Create a new resource."""
        db = info.context["db"]
        user = info.context["user"]
        if not user:
            raise Exception("Authentication required")

        service = YourService(db)
        model = service.create(
            name=input.name,
            description=input.description,
            user_id=user.id
        )
        return YourType.from_model(model)

    @strawberry.mutation
    def update_resource(self, info: Info, input: UpdateYourInput) -> Optional[YourType]:
        """Update resource."""
        db = info.context["db"]
        user = info.context["user"]
        if not user:
            raise Exception("Authentication required")

        service = YourService(db)
        model = service.update(
            id=input.id,
            name=input.name,
            description=input.description
        )
        return YourType.from_model(model) if model else None

    @strawberry.mutation
    def delete_resource(self, info: Info, id: int) -> bool:
        """Delete resource."""
        db = info.context["db"]
        user = info.context["user"]
        if not user:
            raise Exception("Authentication required")

        service = YourService(db)
        return service.delete(id)
```

**Best practices:**
- Define separate input types for create/update
- Use `from_model()` static method for conversions
- Extract user and db from info.context
- Raise clear exceptions for errors
- Use type hints everywhere
- Add docstrings for queries and mutations

#### 5. Import Models in `core/init_db.py`

Add import to `import_all_models()` function:

```python
def import_all_models():
    """Import all models to ensure they are registered with SQLAlchemy."""
    from auth.models.user import UserModel
    from auth.models.role import RoleModel
    from auth.models.permission import PermissionModel
    from auth.models.profile import UserProfileModel
    from languages.models.language import LanguageModel
    from languages.models.concept import ConceptModel
    from languages.models.dictionary import DictionaryModel
    from core.models.file import FileModel
    from core.models.audit_log import AuditLogModel
    from new_module.models.your_model import YourModel  # Add this
```

#### 6. Add Schema Classes to `core/schemas/schema.py`

Update the main schema file:

```python
from new_module.schemas.your_schema import YourQuery, YourMutation

@strawberry.type
class Query(
    LanguageQuery,
    ConceptQuery,
    DictionaryQuery,
    UserQuery,
    RoleQuery,
    FileQuery,
    AuditLogQuery,
    YourQuery,  # Add this
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
    FileMutation,
    YourMutation,  # Add this
):
    pass
```

#### 7. Create Database Migration

```bash
# Generate migration
alembic revision --autogenerate -m "Add your_table"

# Review the generated migration file
# Edit if needed

# Apply migration
alembic upgrade head
```

#### 8. Write Tests

Create `tests/test_your_module.py`:

```python
import pytest
from new_module.services.your_service import YourService
from new_module.models.your_model import YourModel

def test_create_resource(db_session, test_user):
    """Test creating a resource."""
    service = YourService(db_session)
    resource = service.create(
        name="Test Resource",
        description="Test description",
        user_id=test_user.id
    )

    assert resource.id is not None
    assert resource.name == "Test Resource"
    assert resource.description == "Test description"
    assert resource.user_id == test_user.id

def test_get_resource(db_session, test_user):
    """Test retrieving a resource."""
    service = YourService(db_session)
    resource = service.create(
        name="Test Resource",
        description="Test description",
        user_id=test_user.id
    )

    retrieved = service.get_by_id(resource.id)
    assert retrieved is not None
    assert retrieved.id == resource.id
    assert retrieved.name == resource.name

def test_list_resources(db_session, test_user):
    """Test listing resources."""
    service = YourService(db_session)

    # Create multiple resources
    service.create("Resource 1", "Desc 1", test_user.id)
    service.create("Resource 2", "Desc 2", test_user.id)

    resources = service.list_by_user(test_user.id)
    assert len(resources) == 2
```

---

## Database Patterns

### Database Initialization

On startup, `app.py` calls `init_database()` which:
1. Waits for PostgreSQL connection (with retries)
2. Imports all models from all modules
3. Creates tables via `Base.metadata.create_all()`
4. Optionally seeds test data if `SEED_DATABASE=true`

The seeding script is **idempotent** - it checks for existing data and skips creation to avoid duplicates.

### Model Inheritance

All models inherit from `BaseModel`:

```python
from core.models.base import BaseModel

class YourModel(BaseModel):
    __tablename__ = "your_table"
    # Your columns here
```

`BaseModel` provides:
- `id` - Primary key (Integer, auto-increment)
- `created_at` - Timestamp (auto-populated)
- `updated_at` - Timestamp (auto-updated)

### Soft Delete Pattern

For models that need soft delete capability:

```python
from core.models.mixins.soft_delete import SoftDeleteMixin

class YourModel(BaseModel, SoftDeleteMixin):
    __tablename__ = "your_table"
    # Your columns here
```

Usage:

```python
# Soft delete
instance.soft_delete(db, deleted_by_user_id=admin.id)

# Query only active
active_instances = YourModel.active(db).all()

# Query deleted
deleted_instances = YourModel.deleted(db).all()

# Query all (including deleted)
all_instances = YourModel.with_deleted(db).all()

# Restore
instance.restore(db)

# Check if deleted
if instance.is_deleted():
    print("Instance is deleted")
```

### Relationships

Define relationships clearly:

```python
# One-to-many
class User(BaseModel):
    files = relationship("FileModel", back_populates="user")

class File(BaseModel):
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("UserModel", back_populates="files")

# Many-to-many
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("role_id", Integer, ForeignKey("roles.id"))
)

class User(BaseModel):
    roles = relationship("RoleModel", secondary=user_roles, back_populates="users")

class Role(BaseModel):
    users = relationship("UserModel", secondary=user_roles, back_populates="roles")
```

### Database Migrations with Alembic

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Review and edit the generated migration file in alembic/versions/

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

**Best practices:**
- Always review auto-generated migrations
- Never modify database directly
- Test migrations on dev/staging before production
- Keep migrations small and focused
- Add data migrations when needed

---

## Authentication & Security

### JWT-Based Authentication

The application uses JWT (JSON Web Tokens) for authentication:

- **Access tokens** expire in 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Refresh tokens** expire in 7 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
- Passwords hashed with **bcrypt**
- Use `auth/dependencies/` for GraphQL field-level authorization checks

### Test Accounts

Available when `SEED_DATABASE=true`:

- `admin / Admin123!` - Full access (admin role)
- `moderator / Moderator123!` - User management (moderator role)
- `editor / Editor123!` - Content management (editor role)
- `testuser / User123!` - Regular user (user role)

### Authorization Patterns

#### Field-Level Authorization

```python
from auth.dependencies.require_permissions import require_permissions

@strawberry.type
class Query:
    @strawberry.field
    @require_permissions(["admin:read:users"])
    def all_users(self, info: Info) -> List[UserType]:
        """Get all users (admin only)."""
        # Implementation
```

#### Manual Authorization Check

```python
@strawberry.field
def sensitive_data(self, info: Info) -> str:
    user = info.context["user"]
    if not user:
        raise Exception("Authentication required")

    if not user.has_permission("admin:read:sensitive"):
        raise Exception("Insufficient permissions")

    return "Sensitive data"
```

#### Service-Level Authorization

```python
class YourService:
    def create(self, data, user_id: int):
        # Check authorization
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user.has_role("editor"):
            raise Exception("Only editors can create")

        # Business logic
```

### Security Best Practices

**DO:**
- Always validate user input
- Use parameterized queries (SQLAlchemy handles this)
- Hash passwords with bcrypt
- Validate JWT tokens
- Check permissions before sensitive operations
- Use HTTPS in production
- Set strong JWT secrets
- Implement rate limiting
- Log security events

**DON'T:**
- Store passwords in plain text
- Return sensitive data in error messages
- Trust client-side validation
- Use weak JWT secrets
- Disable CORS in production
- Expose internal error details to clients

---

## Environment Configuration

### Key Environment Variables

See `.env.example` for all variables. Key ones:

#### Security

```env
JWT_SECRET_KEY=change_this_to_random_value_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**IMPORTANT:** Change `JWT_SECRET_KEY` in production:
```bash
openssl rand -hex 32
```

#### Database

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=multipult
DB_USER=postgres
DB_PASSWORD=postgres
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
```

#### Redis

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

#### Application

```env
DEBUG=True                    # Set to False in production
SEED_DATABASE=true            # Set to false in production
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
FRONTEND_URL=http://localhost:5173
```

#### Email Configuration

```env
# Development (MailPit)
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=False
FROM_EMAIL=noreply@multipult.dev

# Production (SendGrid/AWS SES)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_sendgrid_api_key
SMTP_USE_TLS=True
FROM_EMAIL=noreply@yourdomain.com
```

#### File Upload

```env
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=10
ALLOWED_EXTENSIONS=png,jpg,jpeg,gif,webp,pdf
```

#### OAuth

```env
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

#### Monitoring

```env
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENVIRONMENT=production
SENTRY_ENABLE_TRACING=true
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Environment-Specific Configs

**Development:**
- `DEBUG=True`
- `SEED_DATABASE=true`
- Use MailPit for emails
- Relaxed CORS
- Detailed error messages

**Staging:**
- `DEBUG=False`
- `SEED_DATABASE=false`
- Production SMTP
- Restricted CORS
- Sentry enabled

**Production:**
- `DEBUG=False`
- `SEED_DATABASE=false`
- Strong passwords
- HTTPS only
- Rate limiting enabled
- Monitoring enabled

---

## Code Style

### PEP 8 Compliance

Follow PEP 8 style guide with these specifics:

#### Line Length

```python
# 100 characters maximum (enforced by black/flake8)
def very_long_function_name_with_many_parameters(
    parameter_one: str, parameter_two: int, parameter_three: Optional[dict] = None
) -> str:
    """Function with many parameters."""
    pass
```

#### Imports

```python
# Standard library imports
import os
import sys
from typing import List, Optional

# Third-party imports
import strawberry
from sqlalchemy import Column, String
from sqlalchemy.orm import Session

# Local application imports
from core.models.base import BaseModel
from auth.models.user import UserModel
```

Sort with `isort`:
```bash
isort . --profile black --line-length 100
```

#### Type Hints

Always use type hints for function signatures:

```python
# Good
def create_user(name: str, email: str, age: Optional[int] = None) -> UserModel:
    """Create a new user."""
    pass

# Bad
def create_user(name, email, age=None):
    pass
```

#### Docstrings

Use docstrings for public functions and classes:

```python
def calculate_total(items: List[dict], tax_rate: float = 0.1) -> float:
    """
    Calculate total price including tax.

    Args:
        items: List of items with 'price' key
        tax_rate: Tax rate as decimal (default 0.1 = 10%)

    Returns:
        Total price including tax

    Raises:
        ValueError: If items list is empty
    """
    if not items:
        raise ValueError("Items list cannot be empty")

    subtotal = sum(item["price"] for item in items)
    return subtotal * (1 + tax_rate)
```

#### Naming Conventions

```python
# Classes: PascalCase
class UserService:
    pass

# Functions/methods: snake_case
def create_user():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 10 * 1024 * 1024

# Private methods: _leading_underscore
def _internal_helper():
    pass

# GraphQL types: PascalCase
@strawberry.type
class UserType:
    pass

# Variables: snake_case
user_count = 10
```

### Async/Await

Use async/await for I/O operations:

```python
# Good - async for I/O
async def send_email(to: str, subject: str, body: str):
    """Send email asynchronously."""
    async with aiohttp.ClientSession() as session:
        await session.post(SMTP_API_URL, json={...})

# Good - sync for CPU-bound or database
def calculate_statistics(data: List[float]) -> dict:
    """Calculate statistics (CPU-bound, use sync)."""
    return {
        "mean": statistics.mean(data),
        "median": statistics.median(data),
    }
```

### Pre-commit Hooks

Enforce code quality with pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black, --line-length=100]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
        args: [--ignore-missing-imports]
```

Install and run:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Tools

```bash
# Format code with black
black . --line-length=100

# Sort imports
isort . --profile black --line-length 100

# Run linter
flake8 . --max-line-length=100 --extend-ignore=E203,W503

# Type checking
mypy . --ignore-missing-imports
```

---

## Testing Strategy

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_app.py             # Application tests
├── test_auth.py            # Authentication tests
├── test_concept.py         # Concept tests
├── test_dictionary.py      # Dictionary tests
├── test_language.py        # Language tests
├── test_admin.py           # Admin tests
└── test_*.py               # Other test files
```

### Test Types

#### Unit Tests

Test services independently:

```python
import pytest
from your_module.services.your_service import YourService

def test_create_resource(db_session):
    """Test resource creation logic."""
    service = YourService(db_session)
    resource = service.create(name="Test", description="Test description")

    assert resource.id is not None
    assert resource.name == "Test"

def test_get_resource_not_found(db_session):
    """Test getting non-existent resource."""
    service = YourService(db_session)
    resource = service.get_by_id(999999)

    assert resource is None
```

#### Integration Tests

Test API endpoints:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_resource_mutation(client: AsyncClient, auth_headers):
    """Test creating resource via GraphQL mutation."""
    query = """
        mutation CreateResource($input: CreateResourceInput!) {
            createResource(input: $input) {
                id
                name
                description
            }
        }
    """
    variables = {
        "input": {
            "name": "Test Resource",
            "description": "Test description"
        }
    }

    response = await client.post(
        "/graphql",
        json={"query": query, "variables": variables},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data
    assert data["data"]["createResource"]["name"] == "Test Resource"
```

### Fixtures

Use `conftest.py` for shared fixtures:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
from auth.models.user import UserModel

@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(db_engine):
    """Create test database session."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user = UserModel(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    return user
```

### Test Configuration

Configure via `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests (fast)
    integration: Integration tests (requires Docker services)
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_app.py

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run with coverage
pytest --cov=. --cov-report=html

# Run and stop on first failure
pytest -x
```

### Test Best Practices

**DO:**
- Write tests for all business logic
- Test both success and failure cases
- Use descriptive test names
- Keep tests independent
- Use fixtures for common setup
- Mock external services
- Test edge cases
- Use appropriate markers (unit/integration)

**DON'T:**
- Test framework code (SQLAlchemy, Strawberry, etc.)
- Write tests that depend on order
- Use production database for tests
- Leave tests commented out
- Test implementation details

---

## CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline is defined in `.github/workflows/ci.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
        run: |
          pytest -v

      - name: Run linter (critical)
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

      - name: Run linter (full)
        run: |
          flake8 . --count --max-line-length=100 --extend-ignore=E203,W503 --statistics

  build:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          docker build -t myapp:${{ github.sha }} .

      - name: Tag and push image
        run: |
          # Push to registry (if configured)
          echo "Built image: myapp:${{ github.sha }}"
```

### Pipeline Stages

1. **Test Stage**
   - Sets up PostgreSQL service container
   - Installs Python 3.11 dependencies
   - Runs pytest with test database
   - Runs flake8 linting (critical errors first, then full analysis)

2. **Build Stage** (only on main branch)
   - Builds Docker image
   - Tags image with commit SHA
   - Pushes to container registry (if configured)

### Local CI Simulation

Run the same checks locally before pushing:

```bash
# Run all pre-commit hooks (includes linting)
pre-commit run --all-files

# Run tests
pytest -v

# Run linter (critical errors)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Run linter (full)
flake8 . --count --max-line-length=100 --extend-ignore=E203,W503 --statistics

# Build Docker image
docker build -t myapp:local .
```

---

## Best Practices

### DRY (Don't Repeat Yourself)

**Good:**
```python
# Centralized business logic
class UserService:
    def create_user(self, username: str, email: str) -> UserModel:
        # Validation and creation logic
        pass

# Use in multiple places
service = UserService(db)
user = service.create_user("john", "john@example.com")
```

**Bad:**
```python
# Duplicated logic in mutations
@strawberry.mutation
def register(username: str, email: str):
    # Validation logic duplicated
    if not username or not email:
        raise Exception("Required fields")
    user = UserModel(username=username, email=email)
    db.add(user)
    db.commit()

@strawberry.mutation
def create_user(username: str, email: str):
    # Same validation logic again
    if not username or not email:
        raise Exception("Required fields")
    user = UserModel(username=username, email=email)
    db.add(user)
    db.commit()
```

### Single Responsibility Principle

Each class/function should have one responsibility:

**Good:**
```python
class EmailService:
    """Handles email sending only."""
    def send_email(self, to: str, subject: str, body: str):
        pass

class UserService:
    """Handles user business logic only."""
    def create_user(self, data: dict):
        pass
```

**Bad:**
```python
class UserService:
    """Does everything - user logic AND email sending."""
    def create_user_and_send_welcome_email(self, data: dict):
        # Create user
        # Send email
        # Too many responsibilities
        pass
```

### Error Handling

**Good:**
```python
@strawberry.mutation
def create_resource(self, info: Info, input: CreateResourceInput):
    try:
        service = YourService(info.context["db"])
        resource = service.create(input.name)
        return YourType.from_model(resource)
    except ValueError as e:
        raise Exception(f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise Exception("Failed to create resource")
```

**Bad:**
```python
@strawberry.mutation
def create_resource(self, info: Info, input: CreateResourceInput):
    # No error handling, exposes internal details
    service = YourService(info.context["db"])
    resource = service.create(input.name)
    return YourType.from_model(resource)
```

### Database Query Optimization

Prevent N+1 queries with eager loading:

**Good:**
```python
from sqlalchemy.orm import joinedload

# Eager load relationships
users = db.query(UserModel).options(
    joinedload(UserModel.profile),
    joinedload(UserModel.roles)
).all()

# Single query instead of N+1
for user in users:
    print(user.profile.first_name)  # No additional query
    print(user.roles)  # No additional query
```

**Bad:**
```python
# Lazy loading causes N+1 queries
users = db.query(UserModel).all()

for user in users:
    print(user.profile.first_name)  # Additional query for each user
    print(user.roles)  # Additional query for each user
```

### Input Validation

Always validate user input:

**Good:**
```python
def create_user(self, username: str, email: str) -> UserModel:
    # Validate
    if not username or len(username) < 3:
        raise ValueError("Username must be at least 3 characters")
    if not email or "@" not in email:
        raise ValueError("Invalid email format")

    # Create
    user = UserModel(username=username, email=email)
    self.db.add(user)
    self.db.commit()
    return user
```

**Bad:**
```python
def create_user(self, username: str, email: str) -> UserModel:
    # No validation, trust client input
    user = UserModel(username=username, email=email)
    self.db.add(user)
    self.db.commit()
    return user
```

### Logging

Use structured logging:

**Good:**
```python
import logging
logger = logging.getLogger(__name__)

def process_order(order_id: int):
    logger.info(f"Processing order", extra={"order_id": order_id})
    try:
        # Process
        logger.info(f"Order processed successfully", extra={"order_id": order_id})
    except Exception as e:
        logger.error(f"Order processing failed", extra={
            "order_id": order_id,
            "error": str(e)
        })
        raise
```

**Bad:**
```python
def process_order(order_id: int):
    print(f"Processing order {order_id}")  # Using print
    try:
        # Process
        print("Done")
    except Exception as e:
        print(f"Error: {e}")  # No context
```

### Configuration Management

Use environment variables, not hardcoded values:

**Good:**
```python
import os

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
MAX_FILE_SIZE = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10")) * 1024 * 1024
```

**Bad:**
```python
SMTP_HOST = "smtp.gmail.com"  # Hardcoded
SMTP_PORT = 587
MAX_FILE_SIZE = 10485760  # Magic number
```

---

## Summary

Key principles:
1. **Modular architecture** - Separate models, services, schemas
2. **Separation of concerns** - Services contain business logic, schemas handle GraphQL
3. **DRY** - Don't repeat yourself, reuse code
4. **Type safety** - Use type hints everywhere
5. **Testing** - Write tests for all business logic
6. **Code quality** - Follow PEP 8, use pre-commit hooks
7. **Security** - Validate input, check permissions, use HTTPS
8. **Documentation** - Add docstrings, keep docs updated

Follow these patterns for consistent, maintainable, production-ready code.
