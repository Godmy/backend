from typing import List, Optional

import strawberry


@strawberry.type
class ConceptLanguage:
    """GraphQL тип для языка в контексте концепции"""

    code: str


@strawberry.type
class ConceptDictionary:
    """GraphQL тип для словаря в контексте концепции"""

    name: str
    description: Optional[str]
    language: ConceptLanguage


@strawberry.type
class Concept:
    """GraphQL тип для концепции"""

    id: int
    parent_id: Optional[int]
    path: str
    depth: int
    dictionaries: List[ConceptDictionary] = strawberry.field(default_factory=list)


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
    def concepts(
        self,
        depth: Optional[int] = None,
        parent_id: Optional[int] = None,
        info: strawberry.Info = None
    ) -> List[Concept]:
        """Получить список концепций с опциональной фильтрацией"""
        from languages.services.concept_service import ConceptService
        from sqlalchemy.orm import joinedload

        # Use DB session from context (no connection leak)
        db = info.context["db"]
        service = ConceptService(db)

        # Determine which service method to call based on filters
        if depth is not None and depth == 0:
            # Get root concepts (depth = 0, no parent)
            concepts = service.get_root_concepts()
        elif parent_id is not None:
            # Get children of specific parent
            concepts = service.get_children(parent_id)
        else:
            # Get all concepts
            concepts = service.get_all()

        # Convert to GraphQL types with dictionaries
        return [
            Concept(
                id=c.id,
                parent_id=c.parent_id,
                path=c.path,
                depth=c.depth,
                dictionaries=[
                    ConceptDictionary(
                        name=d.name,
                        description=d.description,
                        language=ConceptLanguage(code=d.language.code)
                    )
                    for d in c.dictionaries
                ]
            )
            for c in concepts
        ]

    @strawberry.field
    def concept(self, concept_id: int, info: strawberry.Info = None) -> Optional[Concept]:
        """Получить концепцию по ID"""
        from languages.services.concept_service import ConceptService

        # Use DB session from context (no connection leak)
        db = info.context["db"]
        service = ConceptService(db)
        concept = service.get_by_id(concept_id)

        if not concept:
            return None

        return Concept(
            id=concept.id,
            parent_id=concept.parent_id,
            path=concept.path,
            depth=concept.depth,
            dictionaries=[
                ConceptDictionary(
                    name=d.name,
                    description=d.description,
                    language=ConceptLanguage(code=d.language.code)
                )
                for d in concept.dictionaries
            ]
        )


@strawberry.type
class ConceptMutation:
    """GraphQL мутации для концепций"""

    @strawberry.mutation
    def create_concept(self, input: ConceptInput, info: strawberry.Info = None) -> Concept:
        """Создать новую концепцию"""
        from languages.services.concept_service import ConceptService

        # Use DB session from context (no connection leak)
        db = info.context["db"]
        service = ConceptService(db)
        concept = service.create(path=input.path, depth=input.depth, parent_id=input.parent_id)

        return Concept(
            id=concept.id,
            parent_id=concept.parent_id,
            path=concept.path,
            depth=concept.depth,
            dictionaries=[
                ConceptDictionary(
                    name=d.name,
                    description=d.description,
                    language=ConceptLanguage(code=d.language.code)
                )
                for d in concept.dictionaries
            ]
        )

    @strawberry.mutation
    def update_concept(self, concept_id: int, input: ConceptUpdateInput, info: strawberry.Info = None) -> Concept:
        """Обновить концепцию"""
        from languages.services.concept_service import ConceptService

        # Use DB session from context (no connection leak)
        db = info.context["db"]
        service = ConceptService(db)
        concept = service.update(
            concept_id, path=input.path, depth=input.depth, parent_id=input.parent_id
        )

        if not concept:
            raise Exception("Concept not found")

        return Concept(
            id=concept.id,
            parent_id=concept.parent_id,
            path=concept.path,
            depth=concept.depth,
            dictionaries=[
                ConceptDictionary(
                    name=d.name,
                    description=d.description,
                    language=ConceptLanguage(code=d.language.code)
                )
                for d in concept.dictionaries
            ]
        )

    @strawberry.mutation
    def delete_concept(self, concept_id: int, info: strawberry.Info = None) -> bool:
        """Удалить концепцию"""
        from languages.services.concept_service import ConceptService

        # Use DB session from context (no connection leak)
        db = info.context["db"]
        service = ConceptService(db)
        return service.delete(concept_id)
