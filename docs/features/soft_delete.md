# Soft Delete System

Complete soft delete implementation with GraphQL API for managing deleted records.

## Features

- Soft delete mixin for all models (User, Concept, Dictionary, Language)
- Records marked as deleted instead of permanently removed
- Track who deleted the record and when
- Admin-only restore and permanent delete operations
- Query builders for active/deleted/all records
- Automatic filtering of deleted records in queries

## GraphQL API

- **Queries:** [docs/graphql/query/soft_delete.md](../graphql/query/soft_delete.md)
- **Mutations:** [docs/graphql/mutation/soft_delete.md](../graphql/mutation/soft_delete.md)

## Available Entity Types

- `USER` - Users
- `CONCEPT` - Concepts
- `DICTIONARY` - Translations
- `LANGUAGE` - Languages

## Programmatic Usage

### Basic Operations

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

### Advanced Queries

```python
# Get active users with filters
active_editors = (
    UserModel.active(db)
    .join(UserModel.roles)
    .filter(Role.name == "editor")
    .all()
)

# Get deleted users in date range
from datetime import datetime, timedelta

week_ago = datetime.utcnow() - timedelta(days=7)
recently_deleted = (
    UserModel.deleted(db)
    .filter(UserModel.deleted_at >= week_ago)
    .all()
)

# Count deleted records
deleted_count = UserModel.deleted(db).count()
```

### Cascade Behavior

When soft deleting a parent entity:

```python
# Soft delete concept and all its translations
concept.soft_delete(db, deleted_by_user_id=admin.id)

# This will NOT automatically delete related dictionaries
# You need to handle cascade manually if needed
for dictionary in concept.dictionaries:
    dictionary.soft_delete(db, deleted_by_user_id=admin.id)
```

## Implementation

### Model Mixin

```python
from core.models.mixins.soft_delete import SoftDeleteMixin

class MyModel(Base, SoftDeleteMixin):
    __tablename__ = "my_table"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
```

### Mixin Methods

- `soft_delete(db, deleted_by_user_id)` - Mark as deleted
- `restore(db)` - Restore deleted record
- `is_deleted()` - Check deletion status
- `active(db)` - Query builder for active records (class method)
- `deleted(db)` - Query builder for deleted records (class method)
- `with_deleted(db)` - Query builder for all records (class method)

### Database Schema

The mixin adds these columns:
- `deleted_at` (DateTime, nullable, indexed) - Timestamp of deletion
- `deleted_by` (Integer, ForeignKey to User, nullable) - Who deleted it

## Files

- `core/models/mixins/soft_delete.py` - SoftDeleteMixin with all methods
- `core/schemas/soft_delete.py` - GraphQL queries and mutations
- Applied to: UserModel, ConceptModel, DictionaryModel, LanguageModel
- Indexed `deleted_at` column for fast queries
- Foreign key to `deleted_by` user

## Security

### Permissions

- Only admins can view deleted records
- Only admins can restore records
- Only admins can permanently delete
- Permanent delete requires record to be soft-deleted first

### Audit Trail

All soft delete operations are automatically logged:
- Who performed the action
- When it was performed
- What entity was affected
- Original data snapshot

## Migration

### Adding Soft Delete to Existing Models

1. Add mixin to model:
```python
class MyModel(Base, SoftDeleteMixin):
    pass
```

2. Create migration:
```bash
alembic revision --autogenerate -m "Add soft delete to MyModel"
```

3. Review and apply:
```bash
alembic upgrade head
```

### Migrating Existing Data

If you have records that should be marked as deleted:

```python
from datetime import datetime

# Mark existing records as deleted
db.query(MyModel).filter(
    MyModel.status == "archived"
).update({
    "deleted_at": datetime.utcnow(),
    "deleted_by": admin_user.id
})
db.commit()
```

## Best Practices

### When to Use Soft Delete

✅ **Use for:**
- User accounts (regulatory/legal requirements)
- Core business data (audit trail)
- Data with relationships (preserve integrity)
- Undoable operations

❌ **Don't use for:**
- Temporary data (cache, sessions)
- Large volume data (logs, analytics)
- Performance-critical tables
- Data without business value

### Query Performance

```python
# BAD - Loads all records then filters
all_users = db.query(User).all()
active = [u for u in all_users if not u.is_deleted()]

# GOOD - Filters at database level
active_users = User.active(db).all()
```

### Cleanup Strategy

Periodically hard delete old soft-deleted records:

```python
from datetime import datetime, timedelta

# Delete records soft-deleted over 90 days ago
cutoff = datetime.utcnow() - timedelta(days=90)
old_deleted = User.deleted(db).filter(
    User.deleted_at < cutoff
).all()

for user in old_deleted:
    db.delete(user)  # Permanent delete
db.commit()
```

## GraphQL Patterns

### List Deleted Records

For admin dashboards:
```python
# See docs/graphql/query/soft_delete.md for GraphQL examples
```

### Restore with Confirmation

For UI flows:
```python
# 1. Show deleted record details
# 2. Confirm restoration
# 3. Call restore mutation
# 4. Refresh list
```

### Permanent Delete Warning

For destructive operations:
```python
# 1. Verify record is soft-deleted
# 2. Show warning dialog
# 3. Require admin password confirmation
# 4. Call permanent delete mutation
# 5. Update UI
```

## Monitoring

### Track Deletion Rates

```python
from core.metrics import records_deleted_total

# Increment on soft delete
records_deleted_total.labels(entity_type="user").inc()
```

### Alert on Mass Deletions

```promql
# Alert if >100 deletions in 5 minutes
rate(records_deleted_total[5m]) > 100
```

## Troubleshooting

### Records not appearing in queries

Check if they're soft-deleted:
```python
# Use with_deleted() to see all records
all_records = MyModel.with_deleted(db).all()
```

### Cannot delete record

Verify permissions:
```python
if not current_user.has_permission("delete:users"):
    raise PermissionError("Cannot delete users")
```

### Foreign key constraints on restore

Verify related records are also restored:
```python
# Restore parent first
concept.restore(db)

# Then restore children
for dictionary in concept.dictionaries:
    dictionary.restore(db)
```

### Performance issues with large tables

Add index on deleted_at:
```python
# Already included in SoftDeleteMixin
Index('ix_my_model_deleted_at', 'deleted_at')
```

## Related Documentation

- [Audit Logging](audit_logging.md) - Track all deletion operations
- [Admin Panel](admin_panel.md) - UI for managing deleted records
- GraphQL API: [Query](../graphql/query/soft_delete.md) | [Mutation](../graphql/mutation/soft_delete.md)
