# Soft Delete Mutations

**Required:** Admin permission

## Restore Deleted Record

Restore a soft-deleted record.

```graphql
mutation RestoreRecord {
  restoreRecord(entityType: CONCEPT, entityId: 123)  # Returns boolean
}
```

**Available entity types:**
- `USER` - Users
- `CONCEPT` - Concepts
- `DICTIONARY` - Translations
- `LANGUAGE` - Languages

**Actions performed:**
- Clears `deleted_at` field
- Clears `deleted_by` field
- Record becomes active again

---

## Permanently Delete Record

Permanently delete a record from the database (irreversible).

⚠️ **WARNING:** This action is irreversible! Data will be permanently lost.

```graphql
mutation PermanentDelete {
  permanentDelete(entityType: CONCEPT, entityId: 123)  # Returns boolean
}
```

**Requirements:**
- Record must be soft-deleted first
- Admin permission required
- Cannot be undone

**Use cases:**
- GDPR compliance (right to be forgotten)
- Cleanup of old test data
- Remove sensitive data permanently

---

## Programmatic Usage

```python
from auth.models.user import UserModel

# Soft delete
user.soft_delete(db, deleted_by_user_id=admin.id)

# Restore
user.restore(db)

# Check if deleted
if user.is_deleted():
    print("User is deleted")
```

---

## Security

- Only admins can view deleted records
- Only admins can restore records
- Only admins can permanently delete
- Permanent delete requires record to be soft-deleted first
- All actions logged in audit trail

---

## Best Practices

**Use soft delete for:**
- User-initiated deletions
- Content moderation
- Temporary removal
- Accidental deletion recovery

**Use permanent delete for:**
- GDPR/legal requirements
- Sensitive data removal
- Old test data cleanup
- Reducing database size

⚠️ **Always prefer soft delete** unless you have specific requirements for permanent deletion.

---

## Implementation

- `core/models/mixins/soft_delete.py` - SoftDeleteMixin
- `core/schemas/soft_delete.py` - GraphQL mutations
- Indexed `deleted_at` column for fast queries
