"""
Сидер для инициализации языков
Первый этап инициализации БД - все остальные сидеры зависят от языков
"""

import logging

from languages.models import LanguageModel
from scripts.seeders.base import BaseSeeder, SeederMetadata, registry

logger = logging.getLogger(__name__)


@registry.register("languages")
class LanguagesSeeder(BaseSeeder):
    """Инициализация базовых языков системы"""

    @property
    def metadata(self) -> SeederMetadata:
        return SeederMetadata(
            name="languages",
            version="1.0.0",
            description="Инициализация базовых языков системы (8 языков)",
            dependencies=[],  # Нет зависимостей - первый в цепочке
        )

    def should_run(self) -> bool:
        """Проверить, есть ли уже языки в БД"""
        return self.db.query(LanguageModel).first() is None

    def seed(self) -> None:
        """Добавить базовые языки"""
        languages_data = [
            {"code": "ru", "name": "Русский"},
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Español"},
            {"code": "fr", "name": "Français"},
            {"code": "de", "name": "Deutsch"},
            {"code": "zh", "name": "中文"},
            {"code": "ja", "name": "日本語"},
            {"code": "ar", "name": "العربية"},
        ]

        # Используем batch insert для оптимизации
        created = self.batch_insert(LanguageModel, languages_data)

        self.db.commit()
        self.metadata.records_created = created

        self.logger.info(f"Added {created} languages:")
        for lang in languages_data:
            self.logger.info(f"  - {lang['code']}: {lang['name']}")
