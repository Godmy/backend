"""
GraphQL схемы для работы с языками
"""

from .concept import Concept, ConceptMutation, ConceptQuery
from .dictionary import Dictionary, DictionaryMutation, DictionaryQuery
from .language import Language, LanguageMutation, LanguageQuery
from .search import ConceptSearchResult, SearchFilters, SearchQuery, SearchResult
from .dashboard import DashboardCounts, DashboardQuery
from .tag import Tag, TagMutationResult, ConceptQuery as TagConceptQuery, ConceptMutation as TagConceptMutation

__all__ = [
    "Language",
    "LanguageQuery",
    "LanguageMutation",
    "Concept",
    "ConceptQuery",
    "ConceptMutation",
    "Dictionary",
    "DictionaryQuery",
    "DictionaryMutation",
    "SearchQuery",
    "SearchResult",
    "ConceptSearchResult",
    "SearchFilters",
    "DashboardCounts",
    "DashboardQuery",
    "Tag",
    "TagMutationResult",
    "TagConceptQuery",
    "TagConceptMutation",
]
