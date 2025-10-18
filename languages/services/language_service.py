"""
Сервис для работы с языками
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from languages.models.language import LanguageModel


class LanguageService:
    """Сервис для управления языками"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[LanguageModel]:
        """Получить все языки"""
        return self.db.query(LanguageModel).all()

    def get_by_id(self, language_id: int) -> Optional[LanguageModel]:
        """Получить язык по ID"""
        return self.db.query(LanguageModel).filter(LanguageModel.id == language_id).first()

    def get_by_code(self, code: str) -> Optional[LanguageModel]:
        """Получить язык по коду"""
        return self.db.query(LanguageModel).filter(LanguageModel.code == code).first()

    def create(self, code: str, name: str) -> LanguageModel:
        """Создать новый язык"""
        # Проверяем уникальность кода
        existing = self.get_by_code(code)
        if existing:
            raise ValueError(f"Language with code '{code}' already exists")

        language = LanguageModel(code=code, name=name)
        self.db.add(language)
        self.db.commit()
        self.db.refresh(language)
        return language

    def update(
        self, language_id: int, code: Optional[str] = None, name: Optional[str] = None
    ) -> Optional[LanguageModel]:
        """Обновить язык"""
        language = self.get_by_id(language_id)
        if not language:
            return None

        if code is not None:
            # Проверяем уникальность нового кода
            existing = self.get_by_code(code)
            if existing and existing.id != language_id:
                raise ValueError(f"Language with code '{code}' already exists")
            language.code = code

        if name is not None:
            language.name = name

        self.db.commit()
        self.db.refresh(language)
        return language

    def delete(self, language_id: int) -> bool:
        """Удалить язык"""
        language = self.get_by_id(language_id)
        if not language:
            return False

        self.db.delete(language)
        self.db.commit()
        return True
