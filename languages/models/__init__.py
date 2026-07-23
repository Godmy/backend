"""
Модели данных для работы с языками
"""

from .concept import ConceptModel
from .dictionary import DictionaryModel
from .language import LanguageModel
from .tag import ConceptTagModel, TagModel

__all__ = ["LanguageModel", "ConceptModel", "DictionaryModel", "TagModel", "ConceptTagModel"]
