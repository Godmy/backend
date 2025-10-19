from typing import List, Optional

import strawberry


@strawberry.type
class Concept:
    """GraphQL тип для концепции"""

    id: int
    parent_id: Optional[int]
    path: str
    depth: int


@strawberry.input
class ConceptInput:
    """Входные данные для создания концепции"""

    path: str
    depth: int
    parent_id: Optional[int] = None


@strawberry.input
class ConceptUpdateInput:
    """Входные данные для обновления концепции"""

    path: Optional[str] = None
    depth: Optional[int] = None
    parent_id: Optional[int] = None


@strawberry.type
class ConceptQuery:
    """GraphQL запросы для концепций"""

    @strawberry.field
    def concepts(self) -> List[Concept]:
        """Получить список всех концепций"""
        from core.database import get_db
        from languages.services.concept_service import ConceptService

        db = next(get_db())
        service = ConceptService(db)
        concepts = service.get_all()

        return [
            Concept(id=c.id, parent_id=c.parent_id, path=c.path, depth=c.depth) for c in concepts
        ]

    @strawberry.field
    def concept(self, concept_id: int) -> Optional[Concept]:
        """Получить концепцию по ID"""
        from core.database import get_db
        from languages.services.concept_service import ConceptService

        db = next(get_db())
        service = ConceptService(db)
        concept = service.get_by_id(concept_id)

        if not concept:
            return None

        return Concept(
            id=concept.id, parent_id=concept.parent_id, path=concept.path, depth=concept.depth
        )


@strawberry.type
class ConceptMutation:
    """GraphQL мутации для концепций"""

    @strawberry.mutation
    def create_concept(self, input: ConceptInput) -> Concept:
        """Создать новую концепцию"""
        from core.database import get_db
        from languages.services.concept_service import ConceptService

        db = next(get_db())
        service = ConceptService(db)
        concept = service.create(path=input.path, depth=input.depth, parent_id=input.parent_id)

        return Concept(
            id=concept.id, parent_id=concept.parent_id, path=concept.path, depth=concept.depth
        )

    @strawberry.mutation
    def update_concept(self, concept_id: int, input: ConceptUpdateInput) -> Concept:
        """Обновить концепцию"""
        from core.database import get_db
        from languages.services.concept_service import ConceptService

        db = next(get_db())
        service = ConceptService(db)
        concept = service.update(
            concept_id, path=input.path, depth=input.depth, parent_id=input.parent_id
        )

        if not concept:
            raise Exception("Concept not found")

        return Concept(
            id=concept.id, parent_id=concept.parent_id, path=concept.path, depth=concept.depth
        )

    @strawberry.mutation
    def delete_concept(self, concept_id: int) -> bool:
        """Удалить концепцию"""
        from core.database import get_db
        from languages.services.concept_service import ConceptService

        db = next(get_db())
        service = ConceptService(db)
        return service.delete(concept_id)
