"""
Сервис для работы с языками
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from core.decorators.cache import cached
from languages.models.language import LanguageModel


class LanguageService:
    """Сервис для управления языками"""

    def __init__(self, db: Session):
        self.db = db

    @cached(key_prefix="language:list", ttl=3600)  # Cache for 1 hour
    async def get_all(self) -> List[LanguageModel]:
        """Получить все языки"""
        return self.db.query(LanguageModel).all()

    def get_by_id(self, language_id: int) -> Optional[LanguageModel]:
        """Получить язык по ID"""
        return self.db.query(LanguageModel).filter(LanguageModel.id == language_id).first()

    def get_by_code(self, code: str) -> Optional[LanguageModel]:
        """Получить язык по коду"""
        return self.db.query(LanguageModel).filter(LanguageModel.code == code).first()

    async def create(self, code: str, name: str) -> LanguageModel:
        """Создать новый язык"""
        # Import here to avoid circular dependency
        from core.services.cache_service import invalidate_language_cache

        # Проверяем уникальность кода
        existing = self.get_by_code(code)
        if existing:
            raise ValueError(f"Language with code '{code}' already exists")

        language = LanguageModel(code=code, name=name)
        self.db.add(language)
        self.db.commit()
        self.db.refresh(language)

        # Invalidate language cache after successful creation
        await invalidate_language_cache()

        return language

    async def update(
        self, language_id: int, code: Optional[str] = None, name: Optional[str] = None
    ) -> Optional[LanguageModel]:
        """Обновить язык"""
        # Import here to avoid circular dependency
        from core.services.cache_service import invalidate_language_cache

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

        # Invalidate language cache after successful update
        await invalidate_language_cache()

        return language

    async def delete(self, language_id: int) -> bool:
        """Удалить язык"""
        # Import here to avoid circular dependency
        from core.services.cache_service import invalidate_language_cache

        language = self.get_by_id(language_id)
        if not language:
            return False

        self.db.delete(language)
        self.db.commit()

        # Invalidate language cache after successful deletion
        await invalidate_language_cache()

        return True
