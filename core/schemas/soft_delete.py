"""
GraphQL schemas for Soft Delete functionality.

Provides admin-only queries and mutations for managing soft-deleted records.
"""

from typing import List, Optional
import strawberry
from enum import Enum
from datetime import datetime

from auth.models.user import UserModel
from auth.services.permission_service import PermissionService

# ============================================================================
# Enums & Types
# ============================================================================

@strawberry.enum(description="The type of entity that supports soft deletion.")
class SoftDeleteEntityType(str, Enum):
    USER = "user"
    CONCEPT = "concept"
    DICTIONARY = "dictionary"
    LANGUAGE = "language"

@strawberry.type(description="Represents a soft-deleted record.")
class SoftDeletedRecord:
    entity_type: str = strawberry.field(description="The type of the entity.")
    entity_id: int = strawberry.field(description="The ID of the deleted entity.")
    deleted_at: datetime = strawberry.field(description="The timestamp of when the deletion occurred.")
    deleted_by_id: Optional[int] = strawberry.field(description="The ID of the user who performed the deletion.")
    deleted_by_username: Optional[str] = strawberry.field(description="The username of the user who performed the deletion.")

# ============================================================================
# Queries
# ============================================================================

@strawberry.type
class SoftDeleteQuery:
    """GraphQL queries for retrieving soft-deleted records."""

    @strawberry.field(description="""Get a list of soft-deleted records for a given entity type.

**Required permissions:** `admin:read:system`

Example:
```graphql
query GetDeletedConcepts {
  deletedRecords(entityType: CONCEPT, limit: 10) {
    entityId
    deletedAt
    deletedByUsername
  }
}
```
""")
    async def deleted_records(
        self, info: strawberry.Info, entity_type: SoftDeleteEntityType, limit: int = 20, offset: int = 0
    ) -> List[SoftDeletedRecord]:
        from auth.dependencies.auth import get_required_user
        from languages.models.concept import ConceptModel
        from languages.models.dictionary import DictionaryModel
        from languages.models.language import LanguageModel

        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(user, "admin", "read", "system"):
            raise Exception("Admin permission required")

        model_map = {
            "user": UserModel, "concept": ConceptModel,
            "dictionary": DictionaryModel, "language": LanguageModel
        }
        model_class = model_map.get(entity_type.value)
        if not model_class: raise Exception(f"Invalid entity type: {entity_type}")

        limit = min(limit, 100)
        deleted_items = model_class.deleted(db).order_by(model_class.deleted_at.desc()).limit(limit).offset(offset).all()

        results = []
        for record in deleted_items:
            deleted_by_user = db.query(UserModel).filter(UserModel.id == record.deleted_by_id).first() if record.deleted_by_id else None
            results.append(SoftDeletedRecord(
                entity_type=entity_type.value, entity_id=record.id, deleted_at=record.deleted_at,
                deleted_by_id=record.deleted_by_id, deleted_by_username=deleted_by_user.username if deleted_by_user else None
            ))
        return results

# ============================================================================
# Mutations
# ============================================================================

@strawberry.type
class SoftDeleteMutation:
    """GraphQL mutations for managing soft-deleted records."""

    @strawberry.mutation(description="""Restore a soft-deleted record, making it active again.

**Required permissions:** `admin:update:system`

Example:
```graphql
mutation RestoreMyConcept {
  restoreRecord(entityType: CONCEPT, entityId: 123)
}
```
""")
    async def restore_record(self, info: strawberry.Info, entity_type: SoftDeleteEntityType, entity_id: int) -> bool:
        from auth.dependencies.auth import get_required_user
        from languages.models.concept import ConceptModel
        from languages.models.dictionary import DictionaryModel
        from languages.models.language import LanguageModel

        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(user, "admin", "update", "system"):
            raise Exception("Admin permission required")

        model_map = {
            "user": UserModel, "concept": ConceptModel,
            "dictionary": DictionaryModel, "language": LanguageModel
        }
        model_class = model_map.get(entity_type.value)
        if not model_class: raise Exception(f"Invalid entity type: {entity_type}")

        record = model_class.with_deleted(db).filter(model_class.id == entity_id).first()
        if not record: raise Exception(f"{entity_type.value.capitalize()} with ID {entity_id} not found")
        if not record.is_deleted(): raise Exception(f"{entity_type.value.capitalize()} is not deleted")

        record.restore(db)
        return True

    @strawberry.mutation(description="""Permanently delete a record from the database. This action is irreversible.

**Required permissions:** `admin:delete:system`

**WARNING:** The record must be soft-deleted first. This cannot be undone.

Example:
```graphql
mutation HardDeleteConcept {
  permanentDelete(entityType: CONCEPT, entityId: 123)
}
```
""")
    async def permanent_delete(self, info: strawberry.Info, entity_type: SoftDeleteEntityType, entity_id: int) -> bool:
        from auth.dependencies.auth import get_required_user
        from languages.models.concept import ConceptModel
        from languages.models.dictionary import DictionaryModel
        from languages.models.language import LanguageModel

        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(user, "admin", "delete", "system"):
            raise Exception("Admin permission required")

        model_map = {
            "user": UserModel, "concept": ConceptModel,
            "dictionary": DictionaryModel, "language": LanguageModel
        }
        model_class = model_map.get(entity_type.value)
        if not model_class: raise Exception(f"Invalid entity type: {entity_type}")

        record = model_class.with_deleted(db).filter(model_class.id == entity_id).first()
        if not record: raise Exception(f"{entity_type.value.capitalize()} with ID {entity_id} not found")
        if not record.is_deleted(): raise Exception(f"{entity_type.value.capitalize()} must be soft-deleted first")

        db.delete(record)
        db.commit()
        return True
