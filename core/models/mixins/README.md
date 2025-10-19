# Database Model Mixins

Optional mixins for extending model functionality. Each mixin follows the **Single Responsibility Principle**.

## 📁 Structure

```
mixins/
├── __init__.py            # Exports all mixins
├── soft_delete.py         # Soft delete functionality
├── versioned.py           # Version tracking
├── tenant.py              # Multi-tenancy support
├── gdpr.py                # GDPR compliance
├── audit_metadata.py      # IP/User-Agent tracking
├── metadata.py            # Generic JSON metadata
├── combinations.py        # Pre-configured combos
└── README.md              # This file
```

## 🧩 Available Mixins

### SoftDeleteMixin (`soft_delete.py`)
Soft delete instead of permanent deletion.

```python
from core.models.mixins import SoftDeleteMixin

class User(SoftDeleteMixin, BaseModel):
    username = Column(String)

user.soft_delete(db, deleted_by_user_id=admin.id)
active_users = User.active(db).all()
```

### VersionedMixin (`versioned.py`)
Version tracking and optimistic locking.

```python
from core.models.mixins import VersionedMixin

class Concept(VersionedMixin, BaseModel):
    name = Column(String)

# Auto-increments version on update
concept.save(db)  # version++
```

### TenantMixin (`tenant.py`)
Multi-tenant row-level isolation.

```python
from core.models.mixins import TenantMixin

class Document(TenantMixin, BaseModel):
    title = Column(String)

docs = Document.by_tenant(db, tenant_id=123).all()
```

### GDPRMixin (`gdpr.py`)
GDPR compliance (anonymization tracking).

```python
from core.models.mixins import GDPRMixin

class User(GDPRMixin, BaseModel):
    email = Column(String)

user.anonymize(db, anonymized_by_user_id=admin.id)
```

### AuditMetadataMixin (`audit_metadata.py`)
IP addresses and user agents for audit.

```python
from core.models.mixins import AuditMetadataMixin

class Document(AuditMetadataMixin, BaseModel):
    title = Column(String)

doc = Document(
    title="Secret",
    created_by_ip=request.client.host
)
```

### MetadataMixin (`metadata.py`)
Generic JSON metadata storage.

```python
from core.models.mixins import MetadataMixin

class User(MetadataMixin, BaseModel):
    username = Column(String)

user.metadata = {"preferences": {"theme": "dark"}}
```

## 🎨 Pre-configured Combinations

### FullAuditModel (`combinations.py`)
Complete audit trail (soft delete + versioning + audit metadata).

```python
from core.models.mixins import FullAuditModel

class Contract(FullAuditModel):
    amount = Column(Numeric)
```

### TenantAwareModel (`combinations.py`)
Multi-tenant with soft delete.

```python
from core.models.mixins import TenantAwareModel

class Project(TenantAwareModel):
    name = Column(String)
```

## 📚 Documentation

- [BASE_MODEL_GUIDE.md](../../../docs/BASE_MODEL_GUIDE.md) - Full documentation
- [BASE_MODEL_CHEATSHEET.md](../../../docs/BASE_MODEL_CHEATSHEET.md) - Quick reference
- [BASE_MODEL_MIGRATION.md](../../../docs/BASE_MODEL_MIGRATION.md) - Migration guide

## 🎯 SOLID Principles

Each mixin has a **single responsibility**:

| Mixin | Responsibility |
|-------|----------------|
| `SoftDeleteMixin` | Soft deletion lifecycle |
| `VersionedMixin` | Version tracking & change detection |
| `TenantMixin` | Tenant relationship & filtering |
| `GDPRMixin` | Anonymization tracking |
| `AuditMetadataMixin` | Request context tracking |
| `MetadataMixin` | Flexible JSON storage |

## 🔗 Related User Stories

| Mixin | User Story | Priority |
|-------|------------|----------|
| `SoftDeleteMixin` | #6 - Soft Delete | P2 |
| `VersionedMixin` | #13 - Version History | P3 |
| `TenantMixin` | #29 - Multi-Tenancy | P3 |
| `GDPRMixin` | #40 - GDPR Compliance | P2 |
| `AuditMetadataMixin` | #53 - Request Logging | P2 |

See [BACKLOG.md](../../../BACKLOG.md) for full details.
