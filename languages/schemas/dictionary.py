from typing import List, Optional

import strawberry


@strawberry.type
class Dictionary:
    """GraphQL тип для словаря"""

    id: int
    concept_id: int
    language_id: int
    name: str
    description: Optional[str]
    image: Optional[str]


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
        self, concept_id: Optional[int] = None, language_id: Optional[int] = None
    ) -> List[Dictionary]:
        """Получить список словарей с фильтрацией"""
        from core.database import get_db
        from languages.services.dictionary_service import DictionaryService

        db = next(get_db())
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
            )
            for d in dictionaries
        ]

    @strawberry.field
    def dictionary(self, dictionary_id: int) -> Optional[Dictionary]:
        """Получить словарь по ID"""
        from core.database import get_db
        from languages.services.dictionary_service import DictionaryService

        db = next(get_db())
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
        )


@strawberry.type
class DictionaryMutation:
    """GraphQL мутации для словарей"""

    @strawberry.mutation
    def create_dictionary(self, input: DictionaryInput) -> Dictionary:
        """Создать новый словарь"""
        from core.database import get_db
        from languages.services.dictionary_service import DictionaryService

        db = next(get_db())
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
        )

    @strawberry.mutation
    def update_dictionary(self, dictionary_id: int, input: DictionaryUpdateInput) -> Dictionary:
        """Обновить словарь"""
        from core.database import get_db
        from languages.services.dictionary_service import DictionaryService

        db = next(get_db())
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
        )

    @strawberry.mutation
    def delete_dictionary(self, dictionary_id: int) -> bool:
        """Удалить словарь"""
        from core.database import get_db
        from languages.services.dictionary_service import DictionaryService

        db = next(get_db())
        service = DictionaryService(db)
        return service.delete(dictionary_id)
