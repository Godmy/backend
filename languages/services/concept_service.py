"""
Сервис для работы с концепциями
"""

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from core.decorators.cache import cached
from languages.models.concept import ConceptModel


class ConceptService:
    """Сервис для управления концепциями"""

    def __init__(self, db: Session):
        self.db = db

    @cached(key_prefix="concept:list", ttl=300)  # Cache for 5 minutes
    async def get_all(self) -> List[ConceptModel]:
        """Получить все концепции"""
        return (
            self.db.query(ConceptModel)
            .options(joinedload(ConceptModel.dictionaries).joinedload("language"))
            .order_by(ConceptModel.path)
            .all()
        )

    def get_by_id(self, concept_id: int) -> Optional[ConceptModel]:
        """Получить концепцию по ID"""
        return (
            self.db.query(ConceptModel)
            .options(joinedload(ConceptModel.dictionaries).joinedload("language"))
            .filter(ConceptModel.id == concept_id)
            .first()
        )

    def get_by_path(self, path: str) -> Optional[ConceptModel]:
        """Получить концепцию по пути"""
        return (
            self.db.query(ConceptModel)
            .options(joinedload(ConceptModel.dictionaries).joinedload("language"))
            .filter(ConceptModel.path == path)
            .first()
        )

    def get_children(self, parent_id: int) -> List[ConceptModel]:
        """Получить дочерние концепции"""
        return (
            self.db.query(ConceptModel)
            .options(joinedload(ConceptModel.dictionaries).joinedload("language"))
            .filter(ConceptModel.parent_id == parent_id)
            .order_by(ConceptModel.path)
            .all()
        )

    def get_root_concepts(self) -> List[ConceptModel]:
        """Получить корневые концепции (без родителя)"""
        return (
            self.db.query(ConceptModel)
            .options(joinedload(ConceptModel.dictionaries).joinedload("language"))
            .filter(ConceptModel.parent_id.is_(None))
            .order_by(ConceptModel.path)
            .all()
        )

    async def create(self, path: str, depth: int, parent_id: Optional[int] = None) -> ConceptModel:
        """Создать новую концепцию"""
        # Import here to avoid circular dependency
        from core.services.cache_service import invalidate_concept_cache

        # Проверяем существование родительской концепции
        if parent_id is not None:
            parent = self.get_by_id(parent_id)
            if not parent:
                raise ValueError(f"Parent concept with id {parent_id} not found")

        # Проверяем уникальность пути
        existing = self.get_by_path(path)
        if existing:
            raise ValueError(f"Concept with path '{path}' already exists")

        concept = ConceptModel(path=path, depth=depth, parent_id=parent_id)
        self.db.add(concept)
        self.db.commit()
        self.db.refresh(concept)

        # Invalidate concept cache after successful creation
        await invalidate_concept_cache()

        return concept

    async def update(
        self,
        concept_id: int,
        path: Optional[str] = None,
        depth: Optional[int] = None,
        parent_id: Optional[int] = None,
    ) -> Optional[ConceptModel]:
        """Обновить концепцию"""
        # Import here to avoid circular dependency
        from core.services.cache_service import invalidate_concept_cache

        concept = self.get_by_id(concept_id)
        if not concept:
            return None

        if path is not None:
            # Проверяем уникальность нового пути
            existing = self.get_by_path(path)
            if existing and existing.id != concept_id:
                raise ValueError(f"Concept with path '{path}' already exists")
            concept.path = path

        if depth is not None:
            concept.depth = depth

        if parent_id is not None:
            # Проверяем существование родителя
            parent = self.get_by_id(parent_id)
            if not parent:
                raise ValueError(f"Parent concept with id {parent_id} not found")
            # Проверяем, что не создаем циклическую зависимость
            if parent_id == concept_id:
                raise ValueError("Concept cannot be its own parent")
            concept.parent_id = parent_id

        self.db.commit()
        self.db.refresh(concept)

        # Invalidate concept cache after successful update
        await invalidate_concept_cache()

        return concept

    async def delete(self, concept_id: int) -> bool:
        """Удалить концепцию"""
        # Import here to avoid circular dependency
        from core.services.cache_service import invalidate_concept_cache

        concept = self.get_by_id(concept_id)
        if not concept:
            return False

        # Проверяем наличие дочерних концепций
        children = self.get_children(concept_id)
        if children:
            raise ValueError(
                f"Cannot delete concept {concept_id}: " f"it has {len(children)} child concepts"
            )

        self.db.delete(concept)
        self.db.commit()

        # Invalidate concept cache after successful deletion
        await invalidate_concept_cache()

        return True
