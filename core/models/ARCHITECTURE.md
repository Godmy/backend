# Models Architecture

## 📐 Structure Overview

```
core/models/
│
├── base.py                          # BaseModel (Core)
│   └── BaseModel
│       ├── id: int
│       ├── created_at: DateTime
│       ├── updated_at: DateTime
│       └── methods: get_by_id(), save(), delete(), to_dict()
│
└── mixins/                          # Optional Mixins
    │
    ├── __init__.py                  # Exports
    │
    ├── soft_delete.py               # Soft Delete
    │   └── SoftDeleteMixin
    │       ├── deleted_at: DateTime
    │       ├── deleted_by_id: int
    │       └── methods: soft_delete(), restore(), active()
    │
    ├── versioned.py                 # Versioning
    │   └── VersionedMixin
    │       ├── version: int
    │       ├── content_hash: str
    │       └── methods: increment_version(), is_modified()
    │
    ├── tenant.py                    # Multi-Tenancy
    │   └── TenantMixin
    │       ├── tenant_id: int
    │       └── methods: by_tenant()
    │
    ├── gdpr.py                      # GDPR
    │   └── GDPRMixin
    │       ├── is_anonymized: bool
    │       ├── anonymized_at: DateTime
    │       └── methods: anonymize()
    │
    ├── audit_metadata.py            # Audit Metadata
    │   └── AuditMetadataMixin
    │       ├── created_by_ip: str
    │       ├── created_by_user_agent: str
    │       ├── updated_by_ip: str
    │       └── updated_by_user_agent: str
    │
    ├── metadata.py                  # Generic Metadata
    │   └── MetadataMixin
    │       └── metadata: JSON
    │
    └── combinations.py              # Pre-configured Combos
        ├── FullAuditModel
        │   = SoftDelete + Versioned + AuditMetadata + Base
        │
        └── TenantAwareModel
            = Tenant + SoftDelete + Base
```

---

## 🧩 Composition Patterns

### Pattern 1: Minimal (BaseModel only)
```
┌─────────────┐
│  BaseModel  │
├─────────────┤
│ id          │
│ created_at  │
│ updated_at  │
└─────────────┘

class Language(BaseModel):
    code = Column(String)
```

### Pattern 2: Soft Delete
```
┌──────────────────┐     ┌─────────────┐
│ SoftDeleteMixin  │────▶│  BaseModel  │
├──────────────────┤     ├─────────────┤
│ deleted_at       │     │ id          │
│ deleted_by_id    │     │ created_at  │
└──────────────────┘     │ updated_at  │
                         └─────────────┘

class User(SoftDeleteMixin, BaseModel):
    username = Column(String)
```

### Pattern 3: Versioned + Soft Delete
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│ VersionedMixin  │────▶│ SoftDeleteMixin  │────▶│  BaseModel  │
├─────────────────┤     ├──────────────────┤     ├─────────────┤
│ version         │     │ deleted_at       │     │ id          │
│ content_hash    │     │ deleted_by_id    │     │ created_at  │
└─────────────────┘     └──────────────────┘     │ updated_at  │
                                                  └─────────────┘

class Concept(VersionedMixin, SoftDeleteMixin, BaseModel):
    name = Column(String)
```

### Pattern 4: Full Audit (Pre-configured)
```
┌─────────────────┐
│ FullAuditModel  │
├─────────────────┤
│ = SoftDelete    │
│ + Versioned     │
│ + AuditMetadata │
│ + Base          │
└─────────────────┘
         │
         ├─ deleted_at, deleted_by_id
         ├─ version, content_hash
         ├─ created_by_ip, updated_by_ip
         └─ id, created_at, updated_at

class Contract(FullAuditModel):
    amount = Column(Numeric)
```

### Pattern 5: Multi-Tenant
```
┌──────────────┐     ┌──────────────────┐     ┌─────────────┐
│ TenantMixin  │────▶│ SoftDeleteMixin  │────▶│  BaseModel  │
├──────────────┤     ├──────────────────┤     ├─────────────┤
│ tenant_id    │     │ deleted_at       │     │ id          │
└──────────────┘     │ deleted_by_id    │     │ created_at  │
                     └──────────────────┘     │ updated_at  │
                                              └─────────────┘

class Project(TenantMixin, SoftDeleteMixin, BaseModel):
    name = Column(String)

# Or use pre-configured
class Project(TenantAwareModel):
    name = Column(String)
```

---

## 🔄 Data Flow

### Query Flow (with SoftDeleteMixin)

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│ User.active(db)      │  ◀── Uses SoftDeleteMixin
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Filter:              │
│ deleted_at IS NULL   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ SQLAlchemy Query     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Database             │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Active Users Only    │
└──────────────────────┘
```

### Update Flow (with VersionedMixin)

```
┌─────────────────┐
│ concept.save()  │
└────────┬────────┘
         │
         ▼
┌──────────────────────────┐
│ SQLAlchemy Event         │
│ before_update            │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ VersionedMixin           │  ◀── Event Listener
│ increment_version()      │
│ update_hash()            │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ version: 1 → 2           │
│ content_hash: updated    │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Database UPDATE          │
└──────────────────────────┘
```

---

## 🎯 Responsibility Matrix

| Component | Responsibility | Dependencies |
|-----------|----------------|--------------|
| `BaseModel` | Core fields & CRUD | SQLAlchemy Base |
| `SoftDeleteMixin` | Soft deletion | BaseModel |
| `VersionedMixin` | Version tracking | BaseModel, hashlib |
| `TenantMixin` | Tenant filtering | BaseModel, Organization |
| `GDPRMixin` | Anonymization flags | BaseModel |
| `AuditMetadataMixin` | Request context | BaseModel |
| `MetadataMixin` | JSON storage | BaseModel |
| `FullAuditModel` | Full audit combo | All audit mixins |
| `TenantAwareModel` | Multi-tenant combo | Tenant + SoftDelete |

---

## 🔐 Security Considerations

### Tenant Isolation
```python
# ❌ DANGER: Bypasses tenant filtering
users = db.query(User).all()

# ✅ SAFE: Filtered by tenant
users = User.by_tenant(db, tenant_id=request.state.tenant_id).all()
```

### Soft Delete
```python
# ❌ DANGER: Includes deleted records
users = db.query(User).all()

# ✅ SAFE: Only active records
users = User.active(db).all()
```

### GDPR
```python
# Service layer handles actual anonymization
def anonymize_user(db, user, admin_id):
    # 1. Replace personal data
    user.email = f"deleted_{user.id}@local"
    user.username = f"user_{user.id}"

    # 2. Set flag
    user.anonymize(db, anonymized_by_user_id=admin_id)
```

---

## 📊 Performance Optimization

### Indexes
```python
class User(SoftDeleteMixin, BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True)

    # Composite index for common query
    __table_args__ = (
        Index('idx_active_users_email', 'deleted_at', 'email'),
    )
```

### Query Optimization
```python
# ✅ Good: Single query with join
users = User.active(db).options(
    joinedload(User.profile)
).all()

# ❌ Bad: N+1 queries
users = User.active(db).all()
for user in users:
    print(user.profile)  # Separate query each time
```

---

## 🧪 Testing Strategy

### Unit Tests (Per Mixin)
```
tests/models/mixins/
├── test_soft_delete.py
├── test_versioned.py
├── test_tenant.py
├── test_gdpr.py
├── test_audit_metadata.py
└── test_metadata.py
```

### Integration Tests
```
tests/models/
├── test_base.py
└── test_combinations.py
```

---

## 📚 Related Documentation

- [BACKLOG.md](../../BACKLOG.md) - User stories
- [BASE_MODEL_GUIDE.md](../../docs/BASE_MODEL_GUIDE.md) - Full guide
- [BASE_MODEL_REFACTORING.md](../../docs/BASE_MODEL_REFACTORING.md) - SOLID refactoring
- [mixins/README.md](./mixins/README.md) - Mixins overview

---

**SOLID Principles Applied:**
- ✅ Single Responsibility
- ✅ Open/Closed
- ✅ Liskov Substitution
- ✅ Interface Segregation
- ✅ Dependency Inversion

**Updated:** 2025-01-19
