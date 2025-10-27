"""
Orchestrator для управления последовательным запуском сидеров
Обрабатывает зависимости и гарантирует правильный порядок выполнения

Порядок инициализации:
1. Languages (языки) - база для всего
2. Roles (роли и права)
3. Users (пользователи)
4. UI Concepts (интерфейсные переводы)
5. Domain Concepts (онтология человека) - слоями по глубине
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from scripts.seeders.base import BaseSeeder, SeederMetadata, registry

# Импортируем все сидеры для регистрации
from scripts.seeders.auth.roles_seeder import RolesSeeder
from scripts.seeders.auth.users_seeder import UsersSeeder
from scripts.seeders.concepts.domain_concepts_seeder import DomainConceptsSeeder
from scripts.seeders.concepts.ui_concepts_seeder import UIConceptsSeeder
from scripts.seeders.languages.languages_seeder import LanguagesSeeder

logger = logging.getLogger(__name__)


class SeederOrchestrator:
    """
    Управляет последовательным запуском всех сидеров

    Функции:
    - Разрешение зависимостей между сидерами
    - Последовательный запуск в правильном порядке
    - Сбор статистики и отчетов
    - Обработка ошибок
    """

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
        self.results: List[SeederMetadata] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def get_seeders_in_order(self) -> List[BaseSeeder]:
        """
        Получить все сидеры в правильном порядке с учетом зависимостей

        Returns:
            Список сидеров в порядке выполнения
        """
        # Создаем экземпляры всех зарегистрированных сидеров
        all_seeders = registry.get_all_seeders(self.db)

        # Разрешаем зависимости
        sorted_seeders = registry.resolve_dependencies(all_seeders)

        return sorted_seeders

    def run_all(self, skip_if_exists: bool = True) -> List[SeederMetadata]:
        """
        Запустить все сидеры последовательно

        Args:
            skip_if_exists: Пропускать сидеры, если данные уже существуют

        Returns:
            Список метаданных всех запущенных сидеров
        """
        self.start_time = datetime.utcnow()
        self.results = []

        self.logger.info("=" * 80)
        self.logger.info("DATABASE SEEDING ORCHESTRATOR")
        self.logger.info("=" * 80)
        self.logger.info(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        self.logger.info("")

        # Получаем все сидеры в правильном порядке
        seeders = self.get_seeders_in_order()

        self.logger.info(f"Found {len(seeders)} seeders to run:")
        for i, seeder in enumerate(seeders, 1):
            meta = seeder.metadata
            deps = ", ".join(meta.dependencies) if meta.dependencies else "none"
            self.logger.info(f"  {i}. {meta.name} (v{meta.version}) - deps: [{deps}]")

        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("STARTING SEEDING PROCESS")
        self.logger.info("=" * 80)
        self.logger.info("")

        # Запускаем каждый сидер
        for i, seeder in enumerate(seeders, 1):
            meta = seeder.metadata
            self.logger.info(f"\n[{i}/{len(seeders)}] Running: {meta.name}")
            self.logger.info(f"Description: {meta.description}")
            self.logger.info("-" * 80)

            try:
                # Проверяем, нужно ли запускать
                if skip_if_exists and not seeder.should_run():
                    self.logger.info(f"⊘ Skipping {meta.name} - data already exists")
                    meta.status = "skipped"
                    self.results.append(meta)
                    continue

                # Запускаем сидер
                result = seeder.run()
                self.results.append(result)

                if result.status == "completed":
                    self.logger.info(f"✓ {meta.name} completed successfully")
                elif result.status == "skipped":
                    self.logger.info(f"⊘ {meta.name} skipped")
                else:
                    self.logger.warning(f"⚠ {meta.name} finished with status: {result.status}")

            except Exception as e:
                self.logger.error(f"✗ {meta.name} failed: {e}")
                meta.status = "failed"
                self.results.append(meta)

                # Решаем, продолжать ли
                if self._should_stop_on_error(meta):
                    self.logger.error("Critical seeder failed. Stopping orchestration.")
                    break
                else:
                    self.logger.warning("Non-critical seeder failed. Continuing...")

        self.end_time = datetime.utcnow()

        # Выводим финальный отчет
        self._print_summary()

        return self.results

    def run_specific(self, seeder_names: List[str]) -> List[SeederMetadata]:
        """
        Запустить только указанные сидеры

        Args:
            seeder_names: Список имен сидеров для запуска

        Returns:
            Список метаданных запущенных сидеров
        """
        self.start_time = datetime.utcnow()
        self.results = []

        self.logger.info(f"Running specific seeders: {', '.join(seeder_names)}")

        for name in seeder_names:
            try:
                seeder = registry.get_seeder(name, self.db)
                result = seeder.run()
                self.results.append(result)
            except ValueError as e:
                self.logger.error(f"Seeder '{name}' not found: {e}")
            except Exception as e:
                self.logger.error(f"Error running seeder '{name}': {e}")

        self.end_time = datetime.utcnow()
        self._print_summary()

        return self.results

    def _should_stop_on_error(self, meta: SeederMetadata) -> bool:
        """
        Определить, нужно ли останавливать процесс при ошибке

        Критичные сидеры (должны выполниться):
        - languages (без них ничего не работает)

        Args:
            meta: Метаданные упавшего сидера

        Returns:
            True если нужно остановить процесс
        """
        critical_seeders = ["languages"]
        return meta.name in critical_seeders

    def _print_summary(self):
        """Вывести финальный отчет"""
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("SEEDING SUMMARY")
        self.logger.info("=" * 80)

        # Подсчет статистики
        completed = sum(1 for r in self.results if r.status == "completed")
        skipped = sum(1 for r in self.results if r.status == "skipped")
        failed = sum(1 for r in self.results if r.status == "failed")
        total_records = sum(r.records_created for r in self.results)

        self.logger.info(f"Total seeders: {len(self.results)}")
        self.logger.info(f"  ✓ Completed: {completed}")
        self.logger.info(f"  ⊘ Skipped: {skipped}")
        self.logger.info(f"  ✗ Failed: {failed}")
        self.logger.info(f"  Total records created: {total_records:,}")

        # Время выполнения
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            self.logger.info(f"  Duration: {duration:.2f} seconds")

        self.logger.info("")
        self.logger.info("Details by seeder:")
        self.logger.info("-" * 80)

        for result in self.results:
            status_icon = {
                "completed": "✓",
                "skipped": "⊘",
                "failed": "✗",
                "pending": "⋯",
            }.get(result.status, "?")

            self.logger.info(
                f"  {status_icon} {result.name:20s} | "
                f"Status: {result.status:10s} | "
                f"Records: {result.records_created:6,d}"
            )

        self.logger.info("=" * 80)

        # Финальный статус
        if failed > 0:
            self.logger.error("⚠ Seeding completed with errors")
        elif completed > 0:
            self.logger.info("✓ Seeding completed successfully!")
        else:
            self.logger.info("⊘ No seeders were run (all skipped)")
