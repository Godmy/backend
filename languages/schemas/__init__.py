"""
GraphQL схемы для работы с языками
"""

from .language import Language, LanguageQuery, LanguageMutation
from .concept import Concept, ConceptQuery, ConceptMutation
from .dictionary import Dictionary, DictionaryQuery, DictionaryMutation

__all__ = [
    "Language", "LanguageQuery", "LanguageMutation",
    "Concept", "ConceptQuery", "ConceptMutation",
    "Dictionary", "DictionaryQuery", "DictionaryMutation"
]
