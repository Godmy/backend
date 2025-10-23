# Soft Delete Queries

**Required:** Admin permission

## Get Deleted Records

Get list of soft-deleted records by entity type.

```graphql
query DeletedRecords {
  deletedRecords(entityType: CONCEPT, limit: 20, offset: 0) {
    entityType
    entityId
    deletedAt
    deletedByUsername
  }
}
```

**Available entity types:**
- `USER` - Users
- `CONCEPT` - Concepts
- `DICTIONARY` - Translations
- `LANGUAGE` - Languages

**Response fields:**
- `entityType` - Type of entity
- `entityId` - ID of deleted entity
- `deletedAt` - Timestamp of deletion
- `deletedByUsername` - Username of user who deleted it

---

## How Soft Delete Works

**Soft delete** marks records as deleted instead of permanently removing them:

1. Record remains in database
2. `deleted_at` field set to deletion timestamp
3. `deleted_by` field set to user who deleted it
4. Record excluded from normal queries
5. Can be restored by admin
6. Can be permanently deleted by admin

**Query builders:**

```python
from auth.models.user import UserModel

# Query only active (not deleted)
active_users = UserModel.active(db).all()

# Query only deleted
deleted_users = UserModel.deleted(db).all()

# Query all (including deleted)
all_users = UserModel.with_deleted(db).all()

# Check if deleted
if user.is_deleted():
    print("User is deleted")
```

---

## Benefits

- **Recovery** - Restore accidentally deleted data
- **Audit trail** - Track who deleted what and when
- **Compliance** - Meet data retention requirements
- **Safety** - Prevent accidental data loss

---

## Implementation

- `core/models/mixins/soft_delete.py` - SoftDeleteMixin
- `core/schemas/soft_delete.py` - GraphQL API
- Applied to: UserModel, ConceptModel, DictionaryModel, LanguageModel

**Database:**
- Indexed `deleted_at` column for fast queries
- Foreign key to `deleted_by` user
