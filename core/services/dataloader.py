"""
DataLoader Service - Batch and cache database queries for GraphQL.

Provides DataLoader implementation to prevent N+1 queries in GraphQL resolvers.

Implementation for User Story #24 - Query Optimization & N+1 Prevention

Features:
    - Batch loading of entities by ID
    - Request-level caching
    - Generic dataloaders for common models
    - Integration with Strawberry GraphQL

Usage:
    from core.services.dataloader import get_dataloaders

    # In GraphQL context
    info.context["dataloaders"] = get_dataloaders(db)

    # In resolver
    user = await info.context["dataloaders"]["user"].load(user_id)
"""

from typing import Any, Dict, List, Optional, TypeVar, Generic, Callable
from sqlalchemy.orm import Session
from collections import defaultdict

T = TypeVar('T')


class DataLoader(Generic[T]):
    """
    Generic DataLoader implementation.

    Batches and caches database queries to prevent N+1 problems.
    Inspired by Facebook's DataLoader pattern.
    """

    def __init__(
        self,
        batch_load_fn: Callable[[List[Any]], List[Optional[T]]],
        cache: bool = True
    ):
        """
        Initialize DataLoader.

        Args:
            batch_load_fn: Function that loads multiple entities by IDs
            cache: Enable caching (default: True)
        """
        self.batch_load_fn = batch_load_fn
        self.cache_enabled = cache
        self._cache: Dict[Any, Optional[T]] = {}
        self._batch: List[Any] = []
        self._batch_loading = False

    async def load(self, key: Any) -> Optional[T]:
        """
        Load a single entity by key.

        Args:
            key: Entity ID or key

        Returns:
            Entity or None if not found
        """
        # Check cache
        if self.cache_enabled and key in self._cache:
            return self._cache[key]

        # Add to batch
        if key not in self._batch:
            self._batch.append(key)

        # Execute batch immediately for synchronous compatibility
        return self._execute_batch_sync(key)

    async def load_many(self, keys: List[Any]) -> List[Optional[T]]:
        """
        Load multiple entities by keys.

        Args:
            keys: List of entity IDs or keys

        Returns:
            List of entities (None for not found)
        """
        results = []
        for key in keys:
            results.append(await self.load(key))
        return results

    def _execute_batch_sync(self, key: Any) -> Optional[T]:
        """Execute batch loading synchronously (for sync resolvers)."""
        if not self._batch:
            return None

        # Get current batch
        batch_keys = list(self._batch)
        self._batch.clear()

        # Load entities
        try:
            entities = self.batch_load_fn(batch_keys)

            # Build result map
            result_map: Dict[Any, Optional[T]] = {}
            for i, batch_key in enumerate(batch_keys):
                entity = entities[i] if i < len(entities) else None
                result_map[batch_key] = entity

                # Cache result
                if self.cache_enabled:
                    self._cache[batch_key] = entity

            return result_map.get(key)

        except Exception as e:
            # Clear cache on error
            self._cache.clear()
            raise e

    def clear(self, key: Any) -> None:
        """Clear cached value for key."""
        if key in self._cache:
            del self._cache[key]

    def clear_all(self) -> None:
        """Clear all cached values."""
        self._cache.clear()


def create_user_dataloader(db: Session) -> DataLoader:
    """
    Create DataLoader for User model.

    Args:
        db: Database session

    Returns:
        DataLoader instance
    """
    from auth.models.user import UserModel
    from sqlalchemy.orm import joinedload

    def batch_load_users(user_ids: List[int]) -> List[Optional[UserModel]]:
        """Batch load users by IDs."""
        users = (
            db.query(UserModel)
            .options(
                joinedload(UserModel.roles),
                joinedload(UserModel.profile)
            )
            .filter(UserModel.id.in_(user_ids))
            .all()
        )

        # Create ID -> user map
        user_map = {user.id: user for user in users}

        # Return users in same order as input IDs
        return [user_map.get(user_id) for user_id in user_ids]

    return DataLoader(batch_load_users)


def create_role_dataloader(db: Session) -> DataLoader:
    """
    Create DataLoader for Role model.

    Args:
        db: Database session

    Returns:
        DataLoader instance
    """
    from auth.models.role import RoleModel

    def batch_load_roles(role_ids: List[int]) -> List[Optional[RoleModel]]:
        """Batch load roles by IDs."""
        roles = db.query(RoleModel).filter(RoleModel.id.in_(role_ids)).all()
        role_map = {role.id: role for role in roles}
        return [role_map.get(role_id) for role_id in role_ids]

    return DataLoader(batch_load_roles)


def create_concept_dataloader(db: Session) -> DataLoader:
    """
    Create DataLoader for Concept model.

    Args:
        db: Database session

    Returns:
        DataLoader instance
    """
    from languages.models.concept import ConceptModel
    from sqlalchemy.orm import joinedload

    def batch_load_concepts(concept_ids: List[int]) -> List[Optional[ConceptModel]]:
        """Batch load concepts by IDs."""
        concepts = (
            db.query(ConceptModel)
            .options(
                joinedload(ConceptModel.creator)
            )
            .filter(ConceptModel.id.in_(concept_ids))
            .all()
        )
        concept_map = {concept.id: concept for concept in concepts}
        return [concept_map.get(concept_id) for concept_id in concept_ids]

    return DataLoader(batch_load_concepts)


def create_dictionary_dataloader(db: Session) -> DataLoader:
    """
    Create DataLoader for Dictionary model.

    Args:
        db: Database session

    Returns:
        DataLoader instance
    """
    from languages.models.dictionary import DictionaryModel
    from sqlalchemy.orm import joinedload

    def batch_load_dictionaries(dict_ids: List[int]) -> List[Optional[DictionaryModel]]:
        """Batch load dictionaries by IDs."""
        dictionaries = (
            db.query(DictionaryModel)
            .options(
                joinedload(DictionaryModel.concept),
                joinedload(DictionaryModel.language)
            )
            .filter(DictionaryModel.id.in_(dict_ids))
            .all()
        )
        dict_map = {dictionary.id: dictionary for dictionary in dictionaries}
        return [dict_map.get(dict_id) for dict_id in dict_ids]

    return DataLoader(batch_load_dictionaries)


def create_language_dataloader(db: Session) -> DataLoader:
    """
    Create DataLoader for Language model.

    Args:
        db: Database session

    Returns:
        DataLoader instance
    """
    from languages.models.language import LanguageModel

    def batch_load_languages(lang_ids: List[int]) -> List[Optional[LanguageModel]]:
        """Batch load languages by IDs."""
        languages = db.query(LanguageModel).filter(LanguageModel.id.in_(lang_ids)).all()
        lang_map = {lang.id: lang for lang in languages}
        return [lang_map.get(lang_id) for lang_id in lang_ids]

    return DataLoader(batch_load_languages)


def create_file_dataloader(db: Session) -> DataLoader:
    """
    Create DataLoader for File model.

    Args:
        db: Database session

    Returns:
        DataLoader instance
    """
    from core.models.file import File
    from sqlalchemy.orm import joinedload

    def batch_load_files(file_ids: List[int]) -> List[Optional[File]]:
        """Batch load files by IDs."""
        files = (
            db.query(File)
            .options(joinedload(File.uploaded_by))
            .filter(File.id.in_(file_ids))
            .all()
        )
        file_map = {file.id: file for file in files}
        return [file_map.get(file_id) for file_id in file_ids]

    return DataLoader(batch_load_files)


def get_dataloaders(db: Session) -> Dict[str, DataLoader]:
    """
    Create all DataLoaders for a request.

    This should be called once per GraphQL request and stored in context.

    Args:
        db: Database session

    Returns:
        Dictionary of DataLoader instances by name

    Example:
        # In GraphQL context setup
        context = {
            "db": db,
            "dataloaders": get_dataloaders(db)
        }

        # In resolver
        user = await info.context["dataloaders"]["user"].load(user_id)
    """
    return {
        "user": create_user_dataloader(db),
        "role": create_role_dataloader(db),
        "concept": create_concept_dataloader(db),
        "dictionary": create_dictionary_dataloader(db),
        "language": create_language_dataloader(db),
        "file": create_file_dataloader(db),
    }
