"""
Сервис для работы со словарями
"""

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from languages.models.concept import ConceptModel
from languages.models.dictionary import DictionaryModel
from languages.models.language import LanguageModel


class DictionaryService:
    """Сервис для управления словарями"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[DictionaryModel]:
        """Получить все словари с предзагрузкой concept"""
        return (
            self.db.query(DictionaryModel)
            .options(joinedload(DictionaryModel.concept))
            .all()
        )

    def get_by_id(self, dictionary_id: int) -> Optional[DictionaryModel]:
        """Получить словарь по ID с предзагрузкой concept"""
        return (
            self.db.query(DictionaryModel)
            .options(joinedload(DictionaryModel.concept))
            .filter(DictionaryModel.id == dictionary_id)
            .first()
        )

    def get_by_concept(self, concept_id: int) -> List[DictionaryModel]:
        """Получить все словари для концепции с предзагрузкой concept"""
        return (
            self.db.query(DictionaryModel)
            .options(joinedload(DictionaryModel.concept))
            .filter(DictionaryModel.concept_id == concept_id)
            .all()
        )

    def get_by_language(self, language_id: int) -> List[DictionaryModel]:
        """Получить все словари для языка с предзагрузкой concept"""
        return (
            self.db.query(DictionaryModel)
            .options(joinedload(DictionaryModel.concept))
            .filter(DictionaryModel.language_id == language_id)
            .all()
        )

    def get_by_concept_and_language(
        self, concept_id: int, language_id: int
    ) -> List[DictionaryModel]:
        """Получить словари для концепции и языка с предзагрузкой concept"""
        return (
            self.db.query(DictionaryModel)
            .options(joinedload(DictionaryModel.concept))
            .filter(
                DictionaryModel.concept_id == concept_id, DictionaryModel.language_id == language_id
            )
            .all()
        )

    def create(
        self,
        concept_id: int,
        language_id: int,
        name: str,
        description: Optional[str] = None,
        image: Optional[str] = None,
    ) -> DictionaryModel:
        """Создать новый словарь"""
        # Проверяем существование концепции
        concept = self.db.query(ConceptModel).filter(ConceptModel.id == concept_id).first()
        if not concept:
            raise ValueError(f"Concept with id {concept_id} not found")

        # Проверяем существование языка
        language = self.db.query(LanguageModel).filter(LanguageModel.id == language_id).first()
        if not language:
            raise ValueError(f"Language with id {language_id} not found")

        dictionary = DictionaryModel(
            concept_id=concept_id,
            language_id=language_id,
            name=name,
            description=description,
            image=image,
        )
        self.db.add(dictionary)
        self.db.commit()
        self.db.refresh(dictionary)
        return dictionary

    def update(
        self,
        dictionary_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        image: Optional[str] = None,
        concept_id: Optional[int] = None,
        language_id: Optional[int] = None,
    ) -> Optional[DictionaryModel]:
        """Обновить словарь"""
        dictionary = self.get_by_id(dictionary_id)
        if not dictionary:
            return None

        if name is not None:
            dictionary.name = name

        if description is not None:
            dictionary.description = description

        if image is not None:
            dictionary.image = image

        if concept_id is not None:
            # Проверяем существование концепции
            concept = self.db.query(ConceptModel).filter(ConceptModel.id == concept_id).first()
            if not concept:
                raise ValueError(f"Concept with id {concept_id} not found")
            dictionary.concept_id = concept_id

        if language_id is not None:
            # Проверяем существование языка
            language = self.db.query(LanguageModel).filter(LanguageModel.id == language_id).first()
            if not language:
                raise ValueError(f"Language with id {language_id} not found")
            dictionary.language_id = language_id

        self.db.commit()
        self.db.refresh(dictionary)
        return dictionary

    def delete(self, dictionary_id: int) -> bool:
        """Удалить словарь"""
        dictionary = self.get_by_id(dictionary_id)
        if not dictionary:
            return False

        self.db.delete(dictionary)
        self.db.commit()
        return True
