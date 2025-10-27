"""
GraphQL schemas for advanced search and filtering of concepts and translations.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

import strawberry

from languages.schemas.concept import Concept
from languages.schemas.dictionary import Dictionary

# ============================================================================
# Enums & Inputs
# ============================================================================

@strawberry.enum(description="Options for sorting search results.")
class SearchSortEnum(str, Enum):
    RELEVANCE = "relevance"
    ALPHABET = "alphabet"
    DATE = "date"

@strawberry.input(description="A comprehensive set of filters for concept searching.")
class SearchFilters:
    query: Optional[str] = strawberry.field(default=None, description="The search term (case-insensitive).")
    language_ids: Optional[List[int]] = strawberry.field(default=None, description="Filter by a list of language IDs.")
    category_path: Optional[str] = strawberry.field(default=None, description="Filter by concept path prefix (e.g., 'science.physics').")
    from_date: Optional[datetime] = strawberry.field(default=None, description="Filter by creation date (from).")
    to_date: Optional[datetime] = strawberry.field(default=None, description="Filter by creation date (to).")
    sort_by: Optional[SearchSortEnum] = strawberry.field(default=SearchSortEnum.RELEVANCE, description="The sorting order for the results.")
    limit: int = strawberry.field(default=20, description="Maximum number of results to return.")
    offset: int = strawberry.field(default=0, description="Offset for pagination.")

# ============================================================================
# Types
# ============================================================================

@strawberry.type(description="A single search result, containing a concept and its matching translations.")
class ConceptSearchResult:
    concept: Concept = strawberry.field(description="The concept that matched the search.")
    dictionaries: List[Dictionary] = strawberry.field(description="The list of dictionary entries (translations) that matched.")
    relevance_score: Optional[float] = strawberry.field(default=None, description="The relevance score of the result.")

@strawberry.type(description="The complete search response, including results and pagination details.")
class SearchResult:
    results: List[ConceptSearchResult]
    total: int = strawberry.field(description="Total number of matching results.")
    has_more: bool = strawberry.field(description="Indicates if more pages are available.")
    limit: int
    offset: int

# ============================================================================
# Queries
# ============================================================================

@strawberry.type
class SearchQuery:
    """GraphQL queries for searching concepts and getting suggestions."""

    @strawberry.field(description="""Performs a full-text search for concepts with advanced filtering, sorting, and pagination.

Example:
```graphql
query SearchForConcepts {
  searchConcepts(filters: {
    query: "пользователь"
    languageIds: [1, 2]  # Russian and English
    categoryPath: "users"
    sortBy: RELEVANCE
    limit: 10
  }) {
    results {
      concept {
        id
        path
      }
      dictionaries {
        name
        language_id
      }
      relevanceScore
    }
    total
    hasMore
  }
}
```
""")
    def search_concepts(self, info: strawberry.Info, filters: SearchFilters) -> SearchResult:
        from languages.services.search_service import SearchService
        db = info.context["db"]
        service = SearchService(db)

        concepts_db, total = service.search_concepts(
            query=filters.query,
            language_ids=filters.language_ids,
            category_path=filters.category_path,
            from_date=filters.from_date,
            to_date=filters.to_date,
            sort_by=filters.sort_by.value if filters.sort_by else "relevance",
            limit=filters.limit,
            offset=filters.offset,
        )

        results = []
        for concept in concepts_db:
            dictionaries = concept.dictionaries
            if filters.language_ids:
                dictionaries = [d for d in dictionaries if d.language_id in filters.language_ids]

            results.append(ConceptSearchResult(
                concept=Concept(id=concept.id, parent_id=concept.parent_id, path=concept.path, depth=concept.depth),
                dictionaries=[
                    Dictionary(
                        id=d.id, concept_id=d.concept_id, language_id=d.language_id,
                        name=d.name, description=d.description, image=d.image
                    )
                    for d in dictionaries
                ],
            ))

        has_more = (filters.offset + filters.limit) < total
        return SearchResult(results=results, total=total, has_more=has_more, limit=filters.limit, offset=filters.offset)

    @strawberry.field(description="""Get search suggestions for autocomplete functionality.

Returns a list of concept names that start with the provided query string.

Example:
```graphql
query GetSuggestions {
  searchSuggestions(query: "auth", languageId: 1, limit: 5)
}
```
""")
    def search_suggestions(
        self, info: strawberry.Info, query: str, language_id: Optional[int] = None, limit: int = 5
    ) -> List[str]:
        from languages.models.dictionary import DictionaryModel
        db = info.context["db"]
        limit = min(limit, 20)

        search_pattern = f"{query}%"
        q = db.query(DictionaryModel.name).filter(
            DictionaryModel.name.ilike(search_pattern),
            DictionaryModel.deleted_at.is_(None),
        )

        if language_id:
            q = q.filter(DictionaryModel.language_id == language_id)

        suggestions = q.distinct().order_by(DictionaryModel.name).limit(limit).all()
        return [s[0] for s in suggestions]

    @strawberry.field(description="""Get the most popular concepts, ranked by the number of translations they have.

This serves as a proxy for usage and importance.

Example:
```graphql
query GetPopular {
  popularConcepts(limit: 5) {
    concept { id path }
    dictionaries { name }
    relevanceScore # Represents translation count
  }
}
```
""")
    def popular_concepts(self, info: strawberry.Info, limit: int = 10) -> List[ConceptSearchResult]:
        from sqlalchemy import func, text
        from languages.models.dictionary import DictionaryModel
        from languages.services.search_service import SearchService
        db = info.context["db"]
        limit = min(limit, 50)

        popular_concept_ids = (
            db.query(DictionaryModel.concept_id, func.count(DictionaryModel.id).label("translation_count"))
            .filter(DictionaryModel.deleted_at.is_(None))
            .group_by(DictionaryModel.concept_id)
            .order_by(text("translation_count DESC"))
            .limit(limit)
            .all()
        )

        service = SearchService(db)
        results = []
        for concept_id, count in popular_concept_ids:
            concept = service.get_concept_with_dictionaries(concept_id)
            if concept:
                results.append(ConceptSearchResult(
                    concept=Concept(id=concept.id, parent_id=concept.parent_id, path=concept.path, depth=concept.depth),
                    dictionaries=[
                        Dictionary(
                            id=d.id, concept_id=d.concept_id, language_id=d.language_id,
                            name=d.name, description=d.description, image=d.image
                        )
                        for d in concept.dictionaries
                    ],
                    relevance_score=float(count),
                ))
        return results
