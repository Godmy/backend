# BaseModel Mixins - Quick Reference

## 📦 Import Paths

```python
# Base model
from core.models.base import BaseModel

# Individual mixins
from core.models.mixins import (
    SoftDeleteMixin,        # Soft delete
    VersionedMixin,         # Versioning
    TenantMixin,            # Multi-tenancy
    GDPRMixin,              # GDPR compliance
    AuditMetadataMixin,     # IP/User-Agent tracking
    MetadataMixin,          # JSON metadata
)

# Pre-configured combinations
from core.models.mixins import (
    FullAuditModel,         # Combo: soft delete + versioning + audit
    TenantAwareModel,       # Combo: tenant + soft delete
)
```

---

## 🔧 BaseModel Methods

```python
# Get by ID
user = User.get_by_id(db, id=123)

# Get all with pagination
users = User.get_all(db, limit=50, offset=0)

# Count
total = User.count(db)

# Save
user.save(db)

# Delete (hard)
user.delete(db)

# To dict
data = user.to_dict()
```

---

## 🗑️ SoftDeleteMixin

**Fields:** `deleted_at`, `deleted_by_id`, `deleted_by`

**Methods:**
```python
# Soft delete
user.soft_delete(db, deleted_by_user_id=admin.id)

# Restore
user.restore(db)

# Check status
if user.is_deleted():
    print("Deleted")

# Queries
User.active(db).all()         # Non-deleted only
User.deleted(db).all()        # Deleted only
User.with_deleted(db).all()   # All records
```

---

## 📌 VersionedMixin

**Fields:** `version`, `content_hash`

**Methods:**
```python
# Auto-increments on save
concept.name = "Updated"
concept.save(db)  # version: 1 → 2

# Check if modified
if concept.is_modified():
    print("Changed")

# Manual operations
concept.increment_version()
concept.update_hash()
```

**Optimistic Locking:**
```python
if concept.version != expected_version:
    raise GraphQLError("Concurrent modification detected")
```

---

## 🏢 TenantMixin

**Fields:** `tenant_id`, `tenant`

**Methods:**
```python
# Query by tenant
docs = Document.by_tenant(db, tenant_id=123).all()
```

**Middleware:**
```python
# Auto-filter in middleware
request.state.tenant_id = get_tenant_from_subdomain(request)
```

---

## 🔒 GDPRMixin

**Fields:** `is_anonymized`, `anonymized_at`, `anonymized_by_id`, `anonymized_by`

**Methods:**
```python
# Mark as anonymized (flag only)
user.anonymize(db, anonymized_by_user_id=admin.id)

# Full anonymization in service
def anonymize_user(db, user, admin_id):
    user.email = f"deleted_{user.id}@local"
    user.username = f"user_{user.id}"
    user.anonymize(db, admin_id)
```

---

## 📊 AuditMetadataMixin

**Fields:** `created_by_ip`, `created_by_user_agent`, `updated_by_ip`, `updated_by_user_agent`

**Usage:**
```python
doc = Document(
    title="Secret",
    created_by_ip=request.client.host,
    created_by_user_agent=request.headers.get('User-Agent')
)
```

---

## 📦 MetadataMixin

**Fields:** `metadata` (JSON)

**Usage:**
```python
user.metadata = {
    "preferences": {"theme": "dark"},
    "custom_field": "value"
}

# Update nested
user.metadata['preferences']['theme'] = 'light'
flag_modified(user, 'metadata')  # Important!
db.commit()
```

---

## 🎨 Model Examples

### Simple Model
```python
class Language(BaseModel):
    __tablename__ = "languages"
    code = Column(String(10))
    name = Column(String(100))
```

### Soft Delete
```python
class User(SoftDeleteMixin, BaseModel):
    __tablename__ = "users"
    username = Column(String(100))

# Query
active_users = User.active(db).all()
```

### Versioning
```python
class Concept(VersionedMixin, BaseModel):
    __tablename__ = "concepts"
    name = Column(String(255))

# Auto version increment
concept.save(db)  # version++
```

### Multi-Tenant
```python
class Project(TenantAwareModel):  # Built-in combo
    __tablename__ = "projects"
    name = Column(String(255))

# Query
projects = Project.by_tenant(db, tenant_id=123).all()
```

### Full Audit
```python
class Contract(FullAuditModel):  # Built-in combo
    __tablename__ = "contracts"
    amount = Column(Numeric(12, 2))

# Includes: soft delete, versioning, audit metadata
```

### Custom Combo
```python
class Profile(
    TenantMixin,
    GDPRMixin,
    SoftDeleteMixin,
    MetadataMixin,
    BaseModel
):
    __tablename__ = "profiles"
    bio = Column(Text)
```

---

## 🔄 Migration Quick Steps

```bash
# 1. Add mixin to model
class User(SoftDeleteMixin, BaseModel):
    ...

# 2. Generate migration
alembic revision --autogenerate -m "Add soft delete to users"

# 3. Apply migration
alembic upgrade head

# 4. Update queries
# Before: db.query(User).all()
# After:  User.active(db).all()
```

---

## 📝 Common Patterns

### Filter Active Records
```python
# ❌ Wrong (includes deleted)
users = db.query(User).filter(User.email.like('%@gmail.com')).all()

# ✅ Correct
users = User.active(db).filter(User.email.like('%@gmail.com')).all()
```

### Admin View with Deleted
```python
@strawberry.field
def users(self, info: Info, include_deleted: bool = False):
    if include_deleted:
        return User.with_deleted(db).all()
    return User.active(db).all()
```

### Optimistic Locking
```python
@strawberry.mutation
def update_concept(self, info: Info, id: int, input: UpdateInput):
    concept = Concept.get_by_id(db, id)

    if concept.version != input.expected_version:
        raise GraphQLError("Concurrent modification")

    concept.name = input.name
    concept.save(db)  # Auto-increment version
    return concept
```

### Tenant Middleware
```python
class TenantMiddleware:
    async def __call__(self, request, call_next):
        subdomain = request.url.hostname.split('.')[0]
        org = db.query(Organization).filter_by(subdomain=subdomain).first()
        request.state.tenant_id = org.id
        return await call_next(request)
```

### Cleanup Old Deleted
```python
@celery_app.task
def cleanup_old_deleted():
    cutoff = datetime.utcnow() - timedelta(days=90)
    old = db.query(User).filter(User.deleted_at < cutoff).all()
    for user in old:
        db.delete(user)  # Hard delete
    db.commit()
```

---

## ⚠️ Important Notes

1. **Mixin Order Matters:** Rightmost should be BaseModel
   ```python
   # ✅ Correct
   class User(SoftDeleteMixin, BaseModel):
       pass

   # ❌ Wrong
   class User(BaseModel, SoftDeleteMixin):
       pass
   ```

2. **Always Use .active() for Soft Delete Models**
   ```python
   # Default queries WON'T filter deleted records automatically
   User.active(db).all()  # ✅ Correct
   db.query(User).all()   # ⚠️ Includes deleted
   ```

3. **Version Auto-Increments on UPDATE Only**
   ```python
   concept = Concept(name="Test")
   concept.save(db)  # version = 1

   concept.name = "Updated"
   concept.save(db)  # version = 2
   ```

4. **Metadata Requires flag_modified**
   ```python
   from sqlalchemy.orm.attributes import flag_modified

   user.metadata['key'] = 'value'
   flag_modified(user, 'metadata')  # Important!
   db.commit()
   ```

5. **Indexes Are Critical**
   ```python
   # Composite index for common queries
   __table_args__ = (
       Index('idx_active_users', 'deleted_at', 'email'),
   )
   ```

---

## 🔗 Related Docs

- [BASE_MODEL_GUIDE.md](./BASE_MODEL_GUIDE.md) - Full documentation
- [BASE_MODEL_MIGRATION.md](./BASE_MODEL_MIGRATION.md) - Migration examples
- [BACKLOG.md](../BACKLOG.md) - Related user stories

---

**Updated:** 2025-01-19
