from typing import List, Optional, TYPE_CHECKING, Any

import strawberry

if TYPE_CHECKING:
    from languages.schemas.concept import Concept


@strawberry.type
class Dictionary:
    """GraphQL тип для словаря"""

    id: int
    concept_id: int
    language_id: int
    name: str
    description: Optional[str]
    image: Optional[str]
    # concept будет загружен через joinedload и передан при создании объекта
    # Use strawberry.Private with proper type annotation
    concept_model: strawberry.Private[Optional[Any]] = None

    @strawberry.field
    def concept(self) -> Optional[strawberry.LazyType["Concept", "languages.schemas.concept"]]:
        """Получить связанный концепт (уже загружен через joinedload)"""
        from languages.schemas.concept import Concept

        if not self.concept_model:
            return None

        return Concept(
            id=self.concept_model.id,
            parent_id=self.concept_model.parent_id,
            path=self.concept_model.path,
            depth=self.concept_model.depth,
        )


@strawberry.input
class DictionaryInput:
    """Входные данные для создания словаря"""

    concept_id: int
    language_id: int
    name: str
    description: Optional[str] = None
    image: Optional[str] = None


@strawberry.input
class DictionaryUpdateInput:
    """Входные данные для обновления словаря"""

    name: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    concept_id: Optional[int] = None
    language_id: Optional[int] = None


@strawberry.type
class DictionaryQuery:
    """GraphQL запросы для словарей"""

    @strawberry.field
    def dictionaries(
        self, concept_id: Optional[int] = None, language_id: Optional[int] = None, info: strawberry.Info = None
    ) -> List[Dictionary]:
        """Получить список словарей с фильтрацией"""
        from languages.services.dictionary_service import DictionaryService

        # Use DB session from context (no connection leak)
        db = info.context["db"]
        service = DictionaryService(db)

        if concept_id and language_id:
            dictionaries = service.get_by_concept_and_language(concept_id, language_id)
        elif concept_id:
            dictionaries = service.get_by_concept(concept_id)
        elif language_id:
            dictionaries = service.get_by_language(language_id)
        else:
            dictionaries = service.get_all()

        return [
            Dictionary(
                id=d.id,
                concept_id=d.concept_id,
                language_id=d.language_id,
                name=d.name,
                description=d.description,
                image=d.image,
                concept_model=d.concept,  # Pass preloaded concept
            )
            for d in dictionaries
        ]

    @strawberry.field
    def dictionary(self, dictionary_id: int, info: strawberry.Info = None) -> Optional[Dictionary]:
        """Получить словарь по ID"""
        from languages.services.dictionary_service import DictionaryService

        # Use DB session from context (no connection leak)
        db = info.context["db"]
        service = DictionaryService(db)
        dict_item = service.get_by_id(dictionary_id)

        if not dict_item:
            return None

        return Dictionary(
            id=dict_item.id,
            concept_id=dict_item.concept_id,
            language_id=dict_item.language_id,
            name=dict_item.name,
            description=dict_item.description,
            image=dict_item.image,
            concept_model=dict_item.concept,  # Pass preloaded concept
        )


@strawberry.type
class DictionaryMutation:
    """GraphQL мутации для словарей"""

    @strawberry.mutation
    def create_dictionary(self, input: DictionaryInput, info: strawberry.Info = None) -> Dictionary:
        """Создать новый словарь"""
        from languages.services.dictionary_service import DictionaryService

        # Use DB session from context (no connection leak)
        db = info.context["db"]
        service = DictionaryService(db)
        dict_item = service.create(
            concept_id=input.concept_id,
            language_id=input.language_id,
            name=input.name,
            description=input.description,
            image=input.image,
        )

        return Dictionary(
            id=dict_item.id,
            concept_id=dict_item.concept_id,
            language_id=dict_item.language_id,
            name=dict_item.name,
            description=dict_item.description,
            image=dict_item.image,
            concept_model=dict_item.concept,
        )

    @strawberry.mutation
    def update_dictionary(self, dictionary_id: int, input: DictionaryUpdateInput, info: strawberry.Info = None) -> Dictionary:
        """Обновить словарь"""
        from languages.services.dictionary_service import DictionaryService

        # Use DB session from context (no connection leak)
        db = info.context["db"]
        service = DictionaryService(db)
        dict_item = service.update(
            dictionary_id,
            name=input.name,
            description=input.description,
            image=input.image,
            concept_id=input.concept_id,
            language_id=input.language_id,
        )

        if not dict_item:
            raise Exception("Dictionary not found")

        return Dictionary(
            id=dict_item.id,
            concept_id=dict_item.concept_id,
            language_id=dict_item.language_id,
            name=dict_item.name,
            description=dict_item.description,
            image=dict_item.image,
            concept_model=dict_item.concept,
        )

    @strawberry.mutation
    def delete_dictionary(self, dictionary_id: int, info: strawberry.Info = None) -> bool:
        """Удалить словарь"""
        from languages.services.dictionary_service import DictionaryService

        # Use DB session from context (no connection leak)
        db = info.context["db"]
        service = DictionaryService(db)
        return service.delete(dictionary_id)
