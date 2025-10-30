# Architecture

Complete architecture documentation for МультиПУЛЬТ backend.

## Overview

МультиПУЛЬТ is a modern Python backend with GraphQL API for managing templates, concepts, and multilingual content.

**Technology Stack:**
- **Framework:** FastAPI/Starlette
- **GraphQL:** Strawberry GraphQL
- **ORM:** SQLAlchemy
- **Database:** PostgreSQL 14+
- **Cache:** Redis 7+
- **Testing:** pytest
- **Migrations:** Alembic

---

## Modular Architecture

The project follows a **strict modular architecture** where each module is self-contained.

### Module Structure

```
module_name/
├── models/          # SQLAlchemy models (database structure)
├── schemas/         # Strawberry GraphQL schemas (API layer)
└── services/        # Business logic (independent of GraphQL)
```

### Core Modules

**`core/`** - Base infrastructure
- Database connection and configuration
- Base models with common fields
- Shared utilities and middleware
- Email service
- File storage service

**`auth/`** - Authentication & Authorization
- User authentication (JWT)
- User management
- Roles and permissions (RBAC)
- User profiles
- Admin operations

**`languages/`** - Multilingual Content
- Language management
- Concepts (hierarchical structure)
- Dictionaries (translations)
- Search functionality

---

## Separation of Concerns

### 1. Models Layer

**Purpose:** Define database structure and relationships

**Responsibilities:**
- SQLAlchemy ORM model definitions
- Table schema (columns, types, constraints)
- Relationships between tables
- Database-level validations

**Example:**
```python
# auth/models/user.py
from core.models.base import BaseModel

class UserModel(BaseModel):
    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Relationships
    profile = relationship("UserProfileModel", back_populates="user", uselist=False)
    roles = relationship("RoleModel", secondary="user_roles", back_populates="users")
```

**Key Points:**
- Inherit from `core.models.base.BaseModel` (provides `id`, `created_at`, `updated_at`)
- Use type hints
- Define relationships explicitly
- Include indexes for performance

---

### 2. Services Layer

**Purpose:** Business logic and database operations

**Responsibilities:**
- All business logic
- Data validation
- Database queries (CRUD operations)
- Complex operations
- Integration with external services

**Example:**
```python
# auth/services/user_service.py
class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, username: str, email: str, password: str) -> UserModel:
        # Validation
        if self.get_user_by_email(email):
            raise ValueError("Email already exists")

        # Hash password
        password_hash = hash_password(password)

        # Create user
        user = UserModel(
            username=username,
            email=email,
            password_hash=password_hash
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user
```

**Key Points:**
- GraphQL-agnostic (can be reused anywhere)
- Accept database session as dependency
- Return domain models, not GraphQL types
- Raise exceptions for errors
- Use type hints

---

### 3. Schemas Layer

**Purpose:** GraphQL API definition

**Responsibilities:**
- GraphQL types definition
- Queries and mutations
- Input validation
- Authorization checks
- Transform domain models to GraphQL types

**Example:**
```python
# auth/schemas/user.py
import strawberry
from auth.services.user_service import UserService

@strawberry.type
class User:
    id: int
    username: str
    email: str
    is_active: bool

@strawberry.type
class UserMutation:
    @strawberry.mutation
    def register(self, info, input: RegisterInput) -> User:
        db = info.context["db"]
        service = UserService(db)

        # Call service
        user = service.create_user(
            username=input.username,
            email=input.email,
            password=input.password
        )

        # Transform to GraphQL type
        return User(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active
        )
```

**Key Points:**
- Use Strawberry decorators (`@strawberry.type`, `@strawberry.mutation`)
- Handle authentication/authorization
- Call services for business logic
- Transform models to GraphQL types
- Return GraphQL types, not domain models

---

## Data Flow

### Query Flow (with Caching)

```
┌─────────────────────┐
│  GraphQL Request    │
│  (from client)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Schemas Layer      │
│  - Parse input      │
│  - Validate         │
│  - Authorize        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Services Layer     │
│  (@cached decorator)│
└──────────┬──────────┘
           │
      ┌────▼────┐
      │ Redis   │
      │ Cache?  │
      └────┬────┘
       Hit │ Miss
     ┌─────┴─────┐
     │           ▼
     │    ┌─────────────────────┐
     │    │  Models Layer       │
     │    │  - Database query   │
     │    └──────────┬──────────┘
     │               │
     │               ▼
     │    ┌─────────────────────┐
     │    │  PostgreSQL         │
     │    │  (database)         │
     │    └──────────┬──────────┘
     │               │
     │               ▼
     │    ┌─────────────────────┐
     │    │  Cache Result       │
     │    │  (Redis, TTL-based) │
     │    └──────────┬──────────┘
     │               │
     └───────────────┘
           │
           ▼
┌─────────────────────┐
│  Schemas Layer      │
│  - Transform to     │
│    GraphQL type     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  GraphQL Response   │
│  (to client)        │
└─────────────────────┘
```

### Mutation Flow (with Cache Invalidation)

```
┌─────────────────────┐
│ GraphQL Mutation    │
│ (from client)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Schemas Layer      │
│  - Parse input      │
│  - Validate         │
│  - Authorize        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Services Layer     │
│  - Business logic   │
│  - DB operations    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  PostgreSQL         │
│  - Write data       │
│  - Commit           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Invalidate Cache   │
│  (Redis pattern)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  GraphQL Response   │
│  (to client)        │
└─────────────────────┘
```

---

## Schema Integration

All module schemas are unified in `core/schemas/schema.py`:

```python
import strawberry
from auth.schemas.user import UserQuery, UserMutation
from auth.schemas.admin import AdminQuery, AdminMutation
from languages.schemas.language import LanguageQuery, LanguageMutation
# ... other imports

@strawberry.type
class Query(
    UserQuery,
    AdminQuery,
    LanguageQuery,
    ConceptQuery,
    DictionaryQuery,
    RoleQuery,
    FileQuery,
    AuditLogQuery
):
    pass

@strawberry.type
class Mutation(
    UserMutation,
    AdminMutation,
    LanguageMutation,
    ConceptMutation,
    DictionaryMutation,
    AuthMutation,
    RoleMutation,
    FileMutation
):
    pass

schema = strawberry.Schema(Query, Mutation)
```

**Benefits:**
- Single unified schema
- Modular organization
- Easy to add new modules
- Clean separation of concerns

---

## Database Models & Relationships

### Entity Relationship Diagram

```
┌─────────────┐         ┌─────────────┐
│    User     │────1:1──│   Profile   │
└──────┬──────┘         └─────────────┘
       │
       │ N:M (user_roles)
       │
       ▼
┌─────────────┐         ┌─────────────┐
│    Role     │────N:M──│ Permission  │
└─────────────┘         └─────────────┘


┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Language   │────1:N──│ Dictionary  │────N:1──│   Concept   │
└─────────────┘         └─────────────┘         └──────┬──────┘
                                                        │
                                                        │ (self-referential)
                                                        │
                                                        ▼
                                                   parent_id
```

### Core Relationships

**User → Role → Permission** (many-to-many through join tables)
```python
User.roles = relationship("Role", secondary="user_roles")
Role.permissions = relationship("Permission", secondary="role_permissions")
```

**User → Profile** (one-to-one)
```python
User.profile = relationship("UserProfile", back_populates="user", uselist=False)
Profile.user = relationship("User", back_populates="profile")
```

**User → File** (one-to-many, uploaded files)
```python
User.files = relationship("File", back_populates="uploaded_by")
File.uploaded_by = relationship("User", back_populates="files")
```

**User → AuditLog** (one-to-many, activity logs)
```python
User.audit_logs = relationship("AuditLog", back_populates="user")
AuditLog.user = relationship("User", back_populates="audit_logs")
```

**Profile → File** (avatar_file_id foreign key)
```python
Profile.avatar_file_id = Column(Integer, ForeignKey("files.id"))
Profile.avatar = relationship("File")
```

**Language ← Dictionary → Concept** (translations link language to concepts)
```python
Dictionary.language = relationship("Language")
Dictionary.concept = relationship("Concept")
```

**Concept** (hierarchical - self-referential with `parent_id`)
```python
Concept.parent_id = Column(Integer, ForeignKey("concepts.id"))
Concept.parent = relationship("Concept", remote_side=[id])
Concept.children = relationship("Concept", back_populates="parent")
```

Uses **materialized path pattern** (stored in `path` field like `/root/parent/child/`)

---

## Authentication & Authorization

### JWT-based Authentication

**Tokens:**
- **Access Token:** Short-lived (30 minutes), used for API requests
- **Refresh Token:** Long-lived (7 days), used to get new access token

**Flow:**
```
1. User logs in with username/password
2. Backend verifies credentials
3. Backend generates access + refresh tokens
4. Client stores tokens
5. Client sends access token in Authorization header
6. Backend validates token on each request
7. When access token expires, use refresh token to get new one
```

**Token Structure:**
```python
{
  "sub": "user_id",           # Subject (user ID)
  "username": "john",         # Username
  "exp": 1234567890,          # Expiration timestamp
  "type": "access"            # Token type
}
```

---

### Role-Based Access Control (RBAC)

**Hierarchy:**
```
User → has many → Roles → have many → Permissions
```

**Built-in Roles:**
- **admin** - Full system access
- **moderator** - User management
- **editor** - Content management
- **viewer** - Read-only access
- **user** - Basic access

**Permission Format:** `resource:action:scope`

Examples:
- `users:read:all` - Read all users
- `users:update:own` - Update own user
- `content:create:all` - Create any content
- `admin:*:*` - Admin full access

**Checking Permissions:**
```python
from auth.dependencies import require_permission

@strawberry.field
@require_permission("users:read:all")
def users(self, info) -> List[User]:
    # Only users with permission can access
    return get_all_users()
```

---

## Database Initialization

On application startup, `app.py` calls `init_database()`:

```python
def init_database():
    # 1. Wait for PostgreSQL connection (with retries)
    wait_for_postgres()

    # 2. Import all models from all modules
    import_all_models()

    # 3. Create tables via Base.metadata.create_all()
    Base.metadata.create_all(bind=engine)

    # 4. Optionally seed test data if SEED_DATABASE=true
    if settings.SEED_DATABASE:
        seed_database()
```

**Model Discovery:**
```python
# core/init_db.py
def import_all_models():
    # Import all models to ensure they're registered
    from auth.models.user import UserModel
    from auth.models.profile import UserProfileModel
    from auth.models.role import RoleModel
    from languages.models.language import LanguageModel
    from languages.models.concept import ConceptModel
    from languages.models.dictionary import DictionaryModel
    # ... other models
```

**Seeding** (idempotent - checks for existing data):
```python
def seed_database():
    if not LanguageModel.query.count():
        create_languages()

    if not RoleModel.query.count():
        create_roles_and_permissions()

    if not UserModel.query.count():
        create_test_users()
```

---

## Middleware Stack

Application middleware (from innermost to outermost):

```
Application
    ↓
CORS Middleware (handle CORS headers)
    ↓
Security Headers Middleware (add security headers)
    ↓
Request Logging Middleware (log requests/responses)
    ↓
Metrics Middleware (collect Prometheus metrics)
    ↓
Shutdown Middleware (reject requests during shutdown)
    ↓
Starlette/FastAPI
    ↓
GraphQL Router
```

---

## Error Handling

### Exception Hierarchy

```
BaseException
└── Exception
    └── HTTPException (Starlette)
        ├── ValidationError
        ├── AuthenticationError
        ├── PermissionError
        └── NotFoundError
```

### Error Flow

```python
# Service raises exception
def get_user(user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError(f"User {user_id} not found")
    return user

# Schema catches and returns GraphQL error
@strawberry.field
def user(self, info, user_id: int) -> User:
    try:
        user = service.get_user(user_id)
        return transform_to_graphql(user)
    except NotFoundError as e:
        raise GraphQLError(str(e))
```

---

## Performance Considerations

### N+1 Query Prevention

**Problem:** Fetching related data in loops causes N+1 queries

**Solution:** Use `joinedload` or `selectinload`

```python
# Bad - N+1 queries
users = db.query(User).all()
for user in users:
    print(user.profile.first_name)  # Each iteration = 1 query

# Good - 2 queries total
from sqlalchemy.orm import joinedload

users = db.query(User).options(joinedload(User.profile)).all()
for user in users:
    print(user.profile.first_name)  # No additional queries
```

### Connection Pooling

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=5,           # Base pool size
    max_overflow=10,       # Additional connections when needed
    pool_pre_ping=True,    # Test connections before use
    pool_recycle=3600      # Recycle connections after 1 hour
)
```

### Caching Strategy

МультиПУЛЬТ implements a **two-tier caching strategy**:

#### 1. HTTP-Level Caching (Client-Side)

- Cache-Control headers for browser caching
- ETag support for conditional requests (304 Not Modified)
- Configured in `CacheControlMiddleware`

```http
GET /graphql
Cache-Control: max-age=60
ETag: "abc123"
```

See [HTTP Caching Documentation](features/http_caching.md)

#### 2. Service-Level Caching (Redis)

- Application-level caching for expensive queries
- Automatic key generation and serialization
- Graceful fallback when Redis unavailable
- Pattern-based cache invalidation

```python
from core.decorators.cache import cached

class LanguageService:
    @cached(key_prefix="language:list", ttl=3600)  # 1 hour
    async def get_all(self) -> List[LanguageModel]:
        return self.db.query(LanguageModel).all()
```

**Current Implementations:**
- **Languages list:** 1 hour TTL (~90% response time reduction)
- **Concepts list:** 5 minutes TTL (~95% response time reduction)

**Cache Invalidation:**
```python
from core.services.cache_service import invalidate_language_cache

async def create_language(self, code: str, name: str):
    language = LanguageModel(code=code, name=name)
    self.db.add(language)
    self.db.commit()
    # Invalidate cache after mutation
    await invalidate_language_cache()
    return language
```

See [Redis Caching Documentation](features/redis_caching.md) for complete guide.

---

## Security

### Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
password_hash = pwd_context.hash(plain_password)

# Verify password
is_valid = pwd_context.verify(plain_password, password_hash)
```

### SQL Injection Prevention

**SQLAlchemy ORM automatically prevents SQL injection:**
```python
# Safe - parameterized query
user = db.query(User).filter(User.username == username).first()

# Avoid raw SQL unless necessary
# If you must use raw SQL, use parameters:
result = db.execute(
    text("SELECT * FROM users WHERE username = :username"),
    {"username": username}
)
```

### CORS Configuration

```python
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Monitoring & Observability

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Logs automatically include request_id and user_id
logger.info("User logged in")
logger.error("Database connection failed", exc_info=True)
```

### Metrics (Prometheus)

```python
from core.metrics import users_registered_total

# Track metrics
users_registered_total.labels(method='email').inc()
```

### Error Tracking (Sentry)

```python
from core.sentry import capture_exception

try:
    process_payment()
except Exception as e:
    capture_exception(e, user_id=user.id, order_id=order.id)
    raise
```

---

## See Also

- **[Development Guide](DEVELOPMENT.md)** - Local development setup
- **[Patterns & Conventions](PATTERNS.md)** - Code patterns
- **[Features Documentation](features/README.md)** - Feature details
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment
