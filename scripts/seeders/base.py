"""
Базовый класс для всех сидеров
Реализует принципы SOLID:
- Single Responsibility: каждый сидер отвечает за свою модель
- Open/Closed: легко добавлять новые сидеры
- Liskov Substitution: все сидеры взаимозаменяемы
- Interface Segregation: четкий интерфейс
- Dependency Inversion: зависимость от абстракций
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SeederMetadata:
    """Метаданные сидера для отслеживания версий и обновлений"""

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        dependencies: Optional[List[str]] = None,
    ):
        self.name = name
        self.version = version
        self.description = description
        self.dependencies = dependencies or []
        self.last_run: Optional[datetime] = None
        self.status: str = "pending"  # pending, running, completed, failed
        self.records_created: int = 0
        self.records_updated: int = 0
        self.records_skipped: int = 0


class BaseSeeder(ABC):
    """
    Базовый абстрактный класс для всех сидеров

    Каждый сидер должен реализовать:
    - metadata: метаданные сидера
    - should_run(): проверка необходимости запуска
    - seed(): основная логика инициализации
    """

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def metadata(self) -> SeederMetadata:
        """Метаданные сидера"""
        pass

    @abstractmethod
    def should_run(self) -> bool:
        """
        Проверить, нужно ли запускать сидер

        Returns:
            True если сидер должен быть запущен
        """
        pass

    @abstractmethod
    def seed(self) -> None:
        """
        Основная логика инициализации данных
        Должна быть идемпотентной (можно запускать многократно)
        """
        pass

    def run(self) -> SeederMetadata:
        """
        Запустить сидер с обработкой ошибок и логированием

        Returns:
            Метаданные сидера с результатами выполнения
        """
        meta = self.metadata
        meta.status = "running"
        meta.last_run = datetime.utcnow()

        self.logger.info("=" * 60)
        self.logger.info(f"Starting seeder: {meta.name}")
        self.logger.info(f"Description: {meta.description}")
        self.logger.info(f"Version: {meta.version}")
        self.logger.info("=" * 60)

        try:
            # Проверяем, нужно ли запускать
            if not self.should_run():
                self.logger.info(f"Skipping {meta.name} - data already exists")
                meta.status = "skipped"
                return meta

            # Запускаем сидер
            self.seed()

            # Успешное завершение
            meta.status = "completed"
            self.logger.info(f"✓ {meta.name} completed successfully!")
            self.logger.info(f"  Created: {meta.records_created}")
            self.logger.info(f"  Updated: {meta.records_updated}")
            self.logger.info(f"  Skipped: {meta.records_skipped}")

        except Exception as e:
            meta.status = "failed"
            self.logger.error(f"✗ {meta.name} failed: {e}")
            self.db.rollback()
            raise

        return meta

    def batch_insert(
        self, model_class: Any, records: List[Dict[str, Any]], batch_size: int = 1000
    ) -> int:
        """
        Оптимизированная batch-вставка записей

        Args:
            model_class: Класс SQLAlchemy модели
            records: Список словарей с данными
            batch_size: Размер батча

        Returns:
            Количество созданных записей
        """
        total = len(records)
        created = 0

        for i in range(0, total, batch_size):
            batch = records[i : i + batch_size]
            self.db.bulk_insert_mappings(model_class, batch)
            self.db.flush()
            created += len(batch)

            # Логируем прогресс
            if total > batch_size:
                progress = (created / total) * 100
                self.logger.info(
                    f"  Progress: {created}/{total} ({progress:.1f}%) "
                    f"- {model_class.__tablename__}"
                )

        return created

    def batch_update(
        self, model_class: Any, records: List[Dict[str, Any]], batch_size: int = 1000
    ) -> int:
        """
        Оптимизированная batch-обновление записей

        Args:
            model_class: Класс SQLAlchemy модели
            records: Список словарей с данными (должны содержать id)
            batch_size: Размер батча

        Returns:
            Количество обновленных записей
        """
        total = len(records)
        updated = 0

        for i in range(0, total, batch_size):
            batch = records[i : i + batch_size]
            self.db.bulk_update_mappings(model_class, batch)
            self.db.flush()
            updated += len(batch)

            # Логируем прогресс
            if total > batch_size:
                progress = (updated / total) * 100
                self.logger.info(
                    f"  Progress: {updated}/{total} ({progress:.1f}%) "
                    f"- {model_class.__tablename__}"
                )

        return updated


class SeederRegistry:
    """
    Реестр всех сидеров для управления зависимостями и порядком выполнения
    """

    def __init__(self):
        self._seeders: Dict[str, type] = {}

    def register(self, name: str):
        """
        Декоратор для регистрации сидера

        Usage:
            @SeederRegistry.register("languages")
            class LanguagesSeeder(BaseSeeder):
                ...
        """

        def decorator(seeder_class):
            self._seeders[name] = seeder_class
            return seeder_class

        return decorator

    def get_seeder(self, name: str, db: Session) -> BaseSeeder:
        """Получить экземпляр сидера по имени"""
        if name not in self._seeders:
            raise ValueError(f"Seeder '{name}' not registered")
        return self._seeders[name](db)

    def get_all_seeders(self, db: Session) -> List[BaseSeeder]:
        """Получить все зарегистрированные сидеры"""
        return [seeder_class(db) for seeder_class in self._seeders.values()]

    def resolve_dependencies(self, seeders: List[BaseSeeder]) -> List[BaseSeeder]:
        """
        Разрешить зависимости и отсортировать сидеры в правильном порядке

        Args:
            seeders: Список сидеров

        Returns:
            Отсортированный список сидеров с учетом зависимостей
        """
        # Создаем словарь name -> seeder
        seeder_map = {s.metadata.name: s for s in seeders}

        # Топологическая сортировка
        sorted_seeders = []
        visited = set()
        temp_visited = set()

        def visit(name: str):
            if name in temp_visited:
                raise ValueError(f"Circular dependency detected: {name}")
            if name in visited:
                return

            temp_visited.add(name)

            seeder = seeder_map.get(name)
            if seeder:
                for dep in seeder.metadata.dependencies:
                    visit(dep)

                visited.add(name)
                sorted_seeders.append(seeder)

            temp_visited.remove(name)

        for seeder in seeders:
            visit(seeder.metadata.name)

        return sorted_seeders


# Глобальный реестр
registry = SeederRegistry()
