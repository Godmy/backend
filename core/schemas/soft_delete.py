"""
GraphQL schemas for Soft Delete functionality.

Provides queries and mutations for managing soft-deleted records.

Implementation for User Story #6 - Soft Delete для всех моделей (P2)
"""

from typing import List, Optional
import strawberry
from enum import Enum


@strawberry.enum
class SoftDeleteEntityType(str, Enum):
    """Available entity types that support soft delete"""

    USER = "user"
    CONCEPT = "concept"
    DICTIONARY = "dictionary"
    LANGUAGE = "language"


@strawberry.type
class SoftDeletedRecord:
    """Information about a soft-deleted record"""

    entity_type: str
    entity_id: int
    deleted_at: str
    deleted_by_id: Optional[int]
    deleted_by_username: Optional[str]


@strawberry.type
class SoftDeleteQuery:
    """GraphQL queries for soft-deleted records"""

    @strawberry.field
    async def deleted_records(
        self,
        info,
        entity_type: SoftDeleteEntityType,
        limit: int = 20,
        offset: int = 0
    ) -> List[SoftDeletedRecord]:
        """
        Get list of soft-deleted records for an entity type.

        Requires admin permission.

        Args:
            entity_type: Type of entity (user, concept, dictionary, language)
            limit: Number of records to return (max 100)
            offset: Pagination offset

        Returns:
            List of soft-deleted records with metadata

        Example:
            query {
              deletedRecords(entityType: CONCEPT, limit: 20) {
                entityType
                entityId
                deletedAt
                deletedByUsername
              }
            }
        """
        from auth.dependencies.auth import get_required_user
        from auth.services.permission_service import PermissionService
        from core.database import get_db
        from auth.models.user import UserModel
        from languages.models.concept import ConceptModel
        from languages.models.dictionary import DictionaryModel
        from languages.models.language import LanguageModel

        current_user = await get_required_user(info)
        db = next(get_db())

        # Check admin permission
        user = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
        if not PermissionService.check_permission(user, "admin", "read", "all"):
            raise Exception("Admin permission required")

        # Get model class
        model_map = {
            "user": UserModel,
            "concept": ConceptModel,
            "dictionary": DictionaryModel,
            "language": LanguageModel,
        }

        model_class = model_map.get(entity_type.value)
        if not model_class:
            raise Exception(f"Invalid entity type: {entity_type}")

        # Query deleted records
        limit = min(limit, 100)
        deleted = (
            model_class.deleted(db)
            .order_by(model_class.deleted_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        # Build response
        results = []
        for record in deleted:
            deleted_by_user = None
            if record.deleted_by_id:
                deleted_by_user = db.query(UserModel).filter(
                    UserModel.id == record.deleted_by_id
                ).first()

            results.append(
                SoftDeletedRecord(
                    entity_type=entity_type.value,
                    entity_id=record.id,
                    deleted_at=record.deleted_at.isoformat(),
                    deleted_by_id=record.deleted_by_id,
                    deleted_by_username=deleted_by_user.username if deleted_by_user else None
                )
            )

        return results


@strawberry.type
class SoftDeleteMutation:
    """GraphQL mutations for soft delete operations"""

    @strawberry.mutation
    async def restore_record(
        self,
        info,
        entity_type: SoftDeleteEntityType,
        entity_id: int
    ) -> bool:
        """
        Restore a soft-deleted record.

        Requires admin permission.

        Args:
            entity_type: Type of entity to restore
            entity_id: ID of the entity to restore

        Returns:
            True if restored successfully

        Example:
            mutation {
              restoreRecord(entityType: CONCEPT, entityId: 123)
            }
        """
        from auth.dependencies.auth import get_required_user
        from auth.services.permission_service import PermissionService
        from core.database import get_db
        from auth.models.user import UserModel
        from languages.models.concept import ConceptModel
        from languages.models.dictionary import DictionaryModel
        from languages.models.language import LanguageModel

        current_user = await get_required_user(info)
        db = next(get_db())

        # Check admin permission
        user = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
        if not PermissionService.check_permission(user, "admin", "update", "all"):
            raise Exception("Admin permission required")

        # Get model class
        model_map = {
            "user": UserModel,
            "concept": ConceptModel,
            "dictionary": DictionaryModel,
            "language": LanguageModel,
        }

        model_class = model_map.get(entity_type.value)
        if not model_class:
            raise Exception(f"Invalid entity type: {entity_type}")

        # Find deleted record
        record = model_class.with_deleted(db).filter(model_class.id == entity_id).first()

        if not record:
            raise Exception(f"{entity_type.value.capitalize()} with ID {entity_id} not found")

        if not record.is_deleted():
            raise Exception(f"{entity_type.value.capitalize()} is not deleted")

        # Restore
        record.restore(db)

        return True

    @strawberry.mutation
    async def permanent_delete(
        self,
        info,
        entity_type: SoftDeleteEntityType,
        entity_id: int
    ) -> bool:
        """
        Permanently delete a soft-deleted record.

        WARNING: This action is irreversible!
        Requires admin permission.

        Args:
            entity_type: Type of entity to permanently delete
            entity_id: ID of the entity

        Returns:
            True if deleted successfully

        Example:
            mutation {
              permanentDelete(entityType: CONCEPT, entityId: 123)
            }
        """
        from auth.dependencies.auth import get_required_user
        from auth.services.permission_service import PermissionService
        from core.database import get_db
        from auth.models.user import UserModel
        from languages.models.concept import ConceptModel
        from languages.models.dictionary import DictionaryModel
        from languages.models.language import LanguageModel

        current_user = await get_required_user(info)
        db = next(get_db())

        # Check admin permission
        user = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
        if not PermissionService.check_permission(user, "admin", "delete", "all"):
            raise Exception("Admin permission required")

        # Get model class
        model_map = {
            "user": UserModel,
            "concept": ConceptModel,
            "dictionary": DictionaryModel,
            "language": LanguageModel,
        }

        model_class = model_map.get(entity_type.value)
        if not model_class:
            raise Exception(f"Invalid entity type: {entity_type}")

        # Find deleted record
        record = model_class.with_deleted(db).filter(model_class.id == entity_id).first()

        if not record:
            raise Exception(f"{entity_type.value.capitalize()} with ID {entity_id} not found")

        if not record.is_deleted():
            raise Exception(f"{entity_type.value.capitalize()} must be soft-deleted first")

        # Permanent delete
        db.delete(record)
        db.commit()

        return True
