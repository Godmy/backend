"""
GraphQL схемы для поиска концепций и переводов
"""

from datetime import datetime
from typing import List, Optional

import strawberry

from languages.schemas.concept import Concept
from languages.schemas.dictionary import Dictionary


@strawberry.enum
class SearchSortEnum:
    """Варианты сортировки результатов поиска"""

    RELEVANCE = "relevance"
    ALPHABET = "alphabet"
    DATE = "date"


@strawberry.input
class SearchFilters:
    """Фильтры для поиска концепций"""

    query: Optional[str] = None
    language_ids: Optional[List[int]] = None
    category_path: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    sort_by: Optional[SearchSortEnum] = SearchSortEnum.RELEVANCE
    limit: Optional[int] = 20
    offset: Optional[int] = 0


@strawberry.type
class ConceptSearchResult:
    """Результат поиска концепции с переводами"""

    concept: Concept
    dictionaries: List[Dictionary]
    relevance_score: Optional[float] = None


@strawberry.type
class SearchResult:
    """Результаты поиска с метаданными"""

    results: List[ConceptSearchResult]
    total: int
    has_more: bool
    limit: int
    offset: int


@strawberry.type
class SearchQuery:
    """GraphQL запросы для поиска"""

    @strawberry.field
    def search_concepts(self, filters: SearchFilters) -> SearchResult:
        """
        Поиск концепций по ключевым словам с фильтрацией

        Args:
            filters: Фильтры поиска (query, языки, категория, даты, сортировка, пагинация)

        Returns:
            SearchResult с найденными концепциями и метаданными
        """
        from core.database import get_db
        from languages.services.search_service import SearchService

        db = next(get_db())
        service = SearchService(db)

        # Выполняем поиск
        concepts, total = service.search_concepts(
            query=filters.query,
            language_ids=filters.language_ids,
            category_path=filters.category_path,
            from_date=filters.from_date,
            to_date=filters.to_date,
            sort_by=filters.sort_by.value if filters.sort_by else "relevance",
            limit=filters.limit or 20,
            offset=filters.offset or 0,
        )

        # Формируем результаты
        results = []
        for concept in concepts:
            # Получаем словари для концепции (уже загружены через joinedload)
            dictionaries = concept.dictionaries

            # Фильтруем словари по языкам если нужно
            if filters.language_ids:
                dictionaries = [d for d in dictionaries if d.language_id in filters.language_ids]

            # Создаем результат
            concept_result = ConceptSearchResult(
                concept=Concept(
                    id=concept.id,
                    parent_id=concept.parent_id,
                    path=concept.path,
                    depth=concept.depth,
                ),
                dictionaries=[
                    Dictionary(
                        id=d.id,
                        concept_id=d.concept_id,
                        language_id=d.language_id,
                        name=d.name,
                        description=d.description,
                        image=d.image,
                    )
                    for d in dictionaries
                ],
            )
            results.append(concept_result)

        # Определяем есть ли еще результаты
        limit = filters.limit or 20
        offset = filters.offset or 0
        has_more = (offset + limit) < total

        return SearchResult(
            results=results, total=total, has_more=has_more, limit=limit, offset=offset
        )
