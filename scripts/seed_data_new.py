"""
Главный скрипт инициализации базы данных
Использует модульную систему сидеров с принципами SOLID

Этот скрипт заменяет старый seed_data.py и предоставляет:
- Модульную архитектуру с четким разделением ответственности
- Автоматическое разрешение зависимостей между сидерами
- Оптимизированную загрузку больших объемов данных
- Детальную статистику и логирование
- Возможность запуска отдельных сидеров

Последовательность инициализации:
1. Languages (языки) - фундамент системы
2. Roles (роли и права доступа)
3. Users (тестовые пользователи)
4. UI Concepts (интерфейсные переводы)
5. Domain Concepts (онтология аттракторов человека)

Использование:
    # Запустить все сидеры
    python seed_data_new.py

    # Запустить только определенные сидеры
    python seed_data_new.py --seeders languages roles

    # Принудительно пересоздать данные
    python seed_data_new.py --force
"""

import argparse
import logging
import os
import sys

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from scripts.seeders.orchestrator import SeederOrchestrator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description="Database seeding with modular architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all seeders
  python seed_data_new.py

  # Run specific seeders
  python seed_data_new.py --seeders languages ui_concepts

  # Force re-seed (WARNING: may cause duplicates)
  python seed_data_new.py --force

  # Verbose output
  python seed_data_new.py --verbose
        """,
    )

    parser.add_argument(
        "--seeders",
        nargs="+",
        help="Specific seeders to run (e.g., languages roles users)",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-seeding even if data exists (may cause duplicates)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose logging",
    )

    return parser.parse_args()


def main():
    """Главная функция"""
    args = parse_arguments()

    # Настройка уровня логирования
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Starting database seeding with modular architecture")
    logger.info(f"Force mode: {args.force}")

    # Создаем сессию БД
    db = SessionLocal()

    try:
        # Создаем orchestrator
        orchestrator = SeederOrchestrator(db)

        # Запускаем сидеры
        if args.seeders:
            # Запуск конкретных сидеров
            logger.info(f"Running specific seeders: {', '.join(args.seeders)}")
            results = orchestrator.run_specific(args.seeders)
        else:
            # Запуск всех сидеров
            logger.info("Running all seeders in dependency order")
            results = orchestrator.run_all(skip_if_exists=not args.force)

        # Проверка результатов
        failed = sum(1 for r in results if r.status == "failed")
        if failed > 0:
            logger.error(f"Seeding completed with {failed} failures")
            sys.exit(1)
        else:
            logger.info("Seeding completed successfully!")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error during seeding: {e}", exc_info=True)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
