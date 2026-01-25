# Migration Guide: Adopting BaseModel Mixins

Быстрый гайд по добавлению mixins к существующим моделям.

## 🎯 Quick Reference

| Mixin | Use Case | Migration Complexity |
|-------|----------|---------------------|
| `SoftDeleteMixin` | Восстановление удаленных данных | ⭐ Easy |
| `VersionedMixin` | Отслеживание версий, optimistic locking | ⭐⭐ Medium |
| `TenantMixin` | Multi-tenant SaaS | ⭐⭐⭐ Hard |
| `GDPRMixin` | GDPR compliance | ⭐ Easy |
| `AuditMetadataMixin` | Логирование IP/User-Agent | ⭐ Easy |
| `MetadataMixin` | Гибкие настройки | ⭐ Easy |

---

## Example 1: Add Soft Delete to Users

### Current Model

```python
# auth/models/user.py
from core.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
```

### Step 1: Update Model

```python
# auth/models/user.py
from core.models.base import BaseModel, SoftDeleteMixin

class User(SoftDeleteMixin, BaseModel):  # ← Add mixin
    __tablename__ = "users"

    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
```

### Step 2: Generate Migration

```bash
alembic revision --autogenerate -m "Add soft delete to users"
```

**Generated migration:**

```python
# migrations/versions/xxx_add_soft_delete_to_users.py
def upgrade():
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('deleted_by_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_deleted_by', 'users', 'users', ['deleted_by_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_users_deleted_at', 'users', ['deleted_at'])

def downgrade():
    op.drop_index('ix_users_deleted_at', 'users')
    op.drop_constraint('fk_users_deleted_by', 'users', type_='foreignkey')
    op.drop_column('users', 'deleted_by_id')
    op.drop_column('users', 'deleted_at')
```

### Step 3: Apply Migration

```bash
alembic upgrade head
```

### Step 4: Update Service Layer

```python
# auth/services/user_service.py

# ❌ Before
def get_all_users(db: Session):
    return db.query(User).all()

# ✅ After
def get_all_users(db: Session):
    return User.active(db).all()  # Only non-deleted users
```

### Step 5: Update GraphQL Schema (Optional)

```python
# auth/schemas/user.py

@strawberry.type
class UserQuery:
    @strawberry.field
    def users(self, info: Info, include_deleted: bool = False) -> List[UserType]:
        db = info.context['db']

        if include_deleted:
            return User.with_deleted(db).all()
        else:
            return User.active(db).all()

@strawberry.type
class UserMutation:
    @strawberry.mutation
    def delete_user(self, info: Info, user_id: int) -> bool:
        db = info.context['db']
        user = info.context['user']  # Current user

        target_user = User.get_by_id(db, user_id)
        if not target_user:
            raise GraphQLError("User not found")

        # Soft delete
        target_user.soft_delete(db, deleted_by_user_id=user.id)
        return True

    @strawberry.mutation
    def restore_user(self, info: Info, user_id: int) -> bool:
        db = info.context['db']

        target_user = User.get_by_id(db, user_id)
        if not target_user or not target_user.is_deleted():
            raise GraphQLError("User not found or not deleted")

        target_user.restore(db)
        return True
```

---

## Example 2: Add Versioning to Concepts

### Step 1: Update Model

```python
# languages/models/concept.py
from core.models.base import BaseModel, VersionedMixin, SoftDeleteMixin

class ConceptModel(VersionedMixin, SoftDeleteMixin, BaseModel):  # ← Add mixins
    __tablename__ = "concepts"

    name = Column(String(255), nullable=False)
    path = Column(String(500))
    description = Column(Text)
```

### Step 2: Generate & Apply Migration

```bash
alembic revision --autogenerate -m "Add versioning to concepts"
alembic upgrade head
```

### Step 3: Update Mutation with Optimistic Locking

```python
# languages/schemas/concept.py

@strawberry.input
class UpdateConceptInput:
    name: str
    description: Optional[str] = None
    expected_version: int  # ← Add version check

@strawberry.type
class ConceptMutation:
    @strawberry.mutation
    def update_concept(
        self,
        info: Info,
        id: int,
        input: UpdateConceptInput
    ) -> ConceptType:
        db = info.context['db']

        concept = ConceptModel.get_by_id(db, id)
        if not concept:
            raise GraphQLError("Concept not found")

        # Optimistic locking check
        if concept.version != input.expected_version:
            raise GraphQLError(
                "Concept was modified by another user. Please refresh and try again.",
                extensions={
                    "code": "CONCURRENT_MODIFICATION",
                    "current_version": concept.version
                }
            )

        # Update
        concept.name = input.name
        concept.description = input.description
        concept.save(db)  # Auto-increments version

        return concept
```

---

## Example 3: Add Full Audit to Sensitive Models

### Step 1: Use FullAuditModel

```python
# your_module/models/sensitive_document.py
from core.models.base import FullAuditModel

class SensitiveDocument(FullAuditModel):  # ← Pre-configured combo
    """
    Includes:
        - SoftDeleteMixin (deleted_at, deleted_by_id)
        - VersionedMixin (version, content_hash)
        - AuditMetadataMixin (IPs, user agents)
        - BaseModel (id, timestamps)
    """
    __tablename__ = "sensitive_documents"

    title = Column(String(255), nullable=False)
    content = Column(Text)
    classification = Column(String(50))  # "public", "internal", "confidential"
```

### Step 2: Update Service to Capture Metadata

```python
# your_module/services/document_service.py

def create_document(
    db: Session,
    input: CreateDocumentInput,
    user_id: int,
    request_context: dict  # IP, user agent, etc.
) -> SensitiveDocument:

    doc = SensitiveDocument(
        title=input.title,
        content=input.content,
        classification=input.classification,

        # Audit metadata
        created_by_ip=request_context['ip'],
        created_by_user_agent=request_context['user_agent']
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Log to audit trail
    AuditService.log_entity_create(
        db=db,
        user_id=user_id,
        entity_type="sensitive_document",
        entity_id=doc.id,
        ip_address=request_context['ip']
    )

    return doc
```

### Step 3: Update GraphQL Mutation

```python
# your_module/schemas/document.py

@strawberry.type
class DocumentMutation:
    @strawberry.mutation
    def create_document(
        self,
        info: Info,
        input: CreateDocumentInput
    ) -> DocumentType:
        db = info.context['db']
        user = info.context['user']
        request = info.context['request']

        # Prepare request context
        request_context = {
            'ip': request.client.host,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }

        # Create document with audit metadata
        doc = DocumentService.create_document(
            db=db,
            input=input,
            user_id=user.id,
            request_context=request_context
        )

        return doc
```

---

## Common Migration Patterns

### Pattern 1: Batch Update Query Filters

```bash
# Find all queries to update
grep -r "db.query(User)" .

# Before
users = db.query(User).filter(User.email.like('%@gmail.com')).all()

# After
users = User.active(db).filter(User.email.like('%@gmail.com')).all()
```

### Pattern 2: Update Admin Queries

```python
# Add option to view deleted records for admins

@strawberry.field
def all_users(
    self,
    info: Info,
    include_deleted: bool = False  # ← Add parameter
) -> List[UserType]:
    db = info.context['db']
    user = info.context['user']

    # Only admins can see deleted users
    if include_deleted and not user.has_permission('user.view_deleted'):
        raise GraphQLError("Permission denied")

    if include_deleted:
        return User.with_deleted(db).all()
    else:
        return User.active(db).all()
```

### Pattern 3: Data Backfill for Existing Records

```python
# If adding versioning to existing data

# migrations/versions/xxx_backfill_concept_versions.py
def upgrade():
    # Add columns
    op.add_column('concepts', sa.Column('version', sa.Integer(), nullable=True))
    op.add_column('concepts', sa.Column('content_hash', sa.String(64), nullable=True))

    # Backfill data
    connection = op.get_bind()

    # Set version = 1 for all existing records
    connection.execute(
        sa.text("UPDATE concepts SET version = 1 WHERE version IS NULL")
    )

    # Make NOT NULL
    op.alter_column('concepts', 'version', nullable=False)
```

---

## Testing Migration

### Create Test Script

```python
# tests/test_soft_delete_migration.py
import pytest
from auth.models.user import User

def test_soft_delete_user(db):
    """Test soft delete functionality"""
    # Create user
    user = User(username="testuser", email="test@example.com")
    user.save(db)
    user_id = user.id

    # Soft delete
    user.soft_delete(db, deleted_by_user_id=1)

    # Verify not in active query
    active_users = User.active(db).filter_by(id=user_id).first()
    assert active_users is None

    # Verify in deleted query
    deleted_user = User.deleted(db).filter_by(id=user_id).first()
    assert deleted_user is not None
    assert deleted_user.is_deleted() is True

    # Restore
    deleted_user.restore(db)

    # Verify back in active
    restored_user = User.active(db).filter_by(id=user_id).first()
    assert restored_user is not None
    assert restored_user.is_deleted() is False

def test_versioning(db):
    """Test versioning auto-increment"""
    from languages.models.concept import ConceptModel

    # Create
    concept = ConceptModel(name="Test", path="/test")
    concept.save(db)
    assert concept.version == 1

    # Update
    concept.name = "Updated"
    concept.save(db)
    assert concept.version == 2

    # Check hash
    old_hash = concept.content_hash
    concept.description = "New description"
    concept.save(db)
    assert concept.content_hash != old_hash
```

---

## Rollback Strategy

### If Migration Fails

```bash
# Rollback migration
alembic downgrade -1

# Or to specific revision
alembic downgrade <revision_id>
```

### Restore Code

```python
# Remove mixin from model
class User(BaseModel):  # Remove SoftDeleteMixin
    ...

# Revert service changes
def get_all_users(db: Session):
    return db.query(User).all()  # Revert to old query
```

---

## Checklist

Before deploying migration to production:

- [ ] Generate migration with `alembic revision --autogenerate`
- [ ] Review generated migration SQL
- [ ] Test migration on local database
- [ ] Update all queries to use `.active()` / `.by_tenant()` / etc.
- [ ] Update GraphQL schemas (add filters, mutations)
- [ ] Write tests for new functionality
- [ ] Update documentation
- [ ] Test rollback procedure
- [ ] Create database backup before production deployment
- [ ] Monitor query performance after deployment (check indexes)

---

## Performance Considerations

### Index Creation for Large Tables

```python
# For tables with millions of records, create indexes before adding data

def upgrade():
    # Add column
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # Create index CONCURRENTLY (PostgreSQL only)
    # This allows reads/writes to continue during index creation
    op.create_index(
        'ix_users_deleted_at',
        'users',
        ['deleted_at'],
        postgresql_concurrently=True
    )
```

### Batch Updates for Versioning

```python
# If backfilling version column for large table

def upgrade():
    op.add_column('concepts', sa.Column('version', sa.Integer(), nullable=True))

    # Batch update (1000 rows at a time)
    connection = op.get_bind()

    while True:
        result = connection.execute(
            sa.text("""
                UPDATE concepts
                SET version = 1
                WHERE id IN (
                    SELECT id FROM concepts
                    WHERE version IS NULL
                    LIMIT 1000
                )
            """)
        )

        if result.rowcount == 0:
            break

    op.alter_column('concepts', 'version', nullable=False)
```

---

**Next Steps:**

1. Read [BASE_MODEL_GUIDE.md](./BASE_MODEL_GUIDE.md) for detailed mixin documentation
2. Check [BACKLOG.md](../BACKLOG.md) for related user stories
3. Review [ARCHITECTURE.md](../ARCHITECTURE.md) for overall architecture

---

**Updated:** 2025-01-19
