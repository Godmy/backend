"""
GraphQL схемы для поиска концепций и переводов
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

import strawberry

from languages.schemas.concept import Concept
from languages.schemas.dictionary import Dictionary


@strawberry.enum
class SearchSortEnum(str, Enum):
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
    def search_concepts(self, filters: SearchFilters, info: strawberry.Info = None) -> SearchResult:
        """
        Поиск концепций по ключевым словам с фильтрацией

        Args:
            filters: Фильтры поиска (query, языки, категория, даты, сортировка, пагинация)

        Returns:
            SearchResult с найденными концепциями и метаданными
        """
        from languages.services.search_service import SearchService

        # Use DB session from context (no connection leak)
        db = info.context["db"]
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

    @strawberry.field
    def search_suggestions(
        self, query: str, language_id: Optional[int] = None, limit: int = 5, info: strawberry.Info = None
    ) -> List[str]:
        """
        Get search suggestions/autocomplete based on partial query.

        Returns matching dictionary names that start with the query string.
        Useful for autocomplete functionality.

        Args:
            query: Partial search query (e.g., "use")
            language_id: Optional language filter
            limit: Maximum number of suggestions (default: 5, max: 20)

        Returns:
            List of suggested search terms

        Example:
            query {
              searchSuggestions(query: "user", languageId: 1, limit: 5)
            }
        """
        from languages.models.dictionary import DictionaryModel

        # Use DB session from context (no connection leak)
        db = info.context["db"]

        # Limit max suggestions
        limit = min(limit, 20)

        search_pattern = f"{query}%"
        base_query = db.query(DictionaryModel.name).filter(
            DictionaryModel.name.ilike(search_pattern),
            DictionaryModel.deleted_at.is_(None),
        )

        if language_id:
            base_query = base_query.filter(DictionaryModel.language_id == language_id)

        suggestions = (
            base_query.distinct()
            .order_by(DictionaryModel.name)
            .limit(limit)
            .all()
        )

        return [s[0] for s in suggestions]

    @strawberry.field
    def popular_concepts(self, limit: int = 10, info: strawberry.Info = None) -> List[ConceptSearchResult]:
        """
        Get most popular concepts (by translation count).

        Returns concepts that have the most translations across languages,
        which serves as a proxy for popularity.

        Args:
            limit: Number of popular concepts to return (default: 10, max: 50)

        Returns:
            List of popular concepts with their translations

        Example:
            query {
              popularConcepts(limit: 10) {
                concept { id path depth }
                dictionaries { name description }
              }
            }
        """
        from sqlalchemy import func, text
        from languages.models.dictionary import DictionaryModel
        from languages.services.search_service import SearchService

        # Use DB session from context (no connection leak)
        db = info.context["db"]

        # Limit max results
        limit = min(limit, 50)

        # Get concepts with most translations
        popular_concept_ids = (
            db.query(
                DictionaryModel.concept_id,
                func.count(DictionaryModel.id).label("translation_count"),
            )
            .filter(DictionaryModel.deleted_at.is_(None))
            .group_by(DictionaryModel.concept_id)
            .order_by(text("translation_count DESC"))
            .limit(limit)
            .all()
        )

        # Get full concept data
        service = SearchService(db)
        results = []

        for concept_id, count in popular_concept_ids:
            concept = service.get_concept_with_dictionaries(concept_id)
            if concept:
                results.append(
                    ConceptSearchResult(
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
                            for d in concept.dictionaries
                        ],
                        relevance_score=float(count),  # Use translation count as score
                    )
                )

        return results
