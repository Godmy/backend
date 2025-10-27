"""
Модуль инициализации базы данных
Отвечает за ожидание подключения к БД, создание таблиц и регистрацию всех моделей
"""

import logging
import time

from sqlalchemy import exc, text

from core.database import Base, engine

logger = logging.getLogger(__name__)


def wait_for_db(max_retries: int = 30, delay: int = 2) -> bool:
    """
    Ожидает доступности базы данных

    Args:
        max_retries: Максимальное количество попыток подключения
        delay: Задержка между попытками в секундах

    Returns:
        True если подключение успешно

    Raises:
        OperationalError: Если не удалось подключиться после всех попыток
    """
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except exc.OperationalError as e:
            if i < max_retries - 1:
                logger.warning(
                    f"Database not ready, retrying in {delay}s... " f"({i+1}/{max_retries})"
                )
                time.sleep(delay)
            else:
                logger.error(f"Could not connect to database after {max_retries} retries: {e}")
                raise
    return False


def import_all_models():
    """
    Импортирует все модели, чтобы они зарегистрировались в Base.metadata
    Это необходимо для корректного создания таблиц
    """
    # Импортируем модели из модуля auth (ПЕРВЫМИ, т.к. на них ссылаются другие модели)
    from auth.models import permission, profile, role, oauth, user

    # Импортируем модели из core
    from core.models import audit_log, file

    # Импортируем модели из модуля languages
    from languages.models import concept, dictionary, language

    logger.info("All models imported successfully")


def create_tables():
    """
    Создает все таблицы в базе данных

    Raises:
        Exception: Если произошла ошибка при создании таблиц
    """
    try:
        logger.info("Creating database tables...")

        # Импортируем все модели
        import_all_models()

        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)

        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise


def init_database(seed: bool = True):
    """
    Полная инициализация базы данных:
    1. Ожидание доступности БД
    2. Создание таблиц
    3. Опционально: заполнение тестовыми данными

    Args:
        seed: Если True, то после создания таблиц запускается скрипт seed_data
    """
    logger.info("=" * 70)
    logger.info("DATABASE INITIALIZATION".center(70))
    logger.info("=" * 70)

    # Шаг 1: Ожидание БД
    logger.info("\n[1/3] Waiting for database connection...")
    wait_for_db()
    logger.info("✓ Database connection established")

    # Шаг 2: Создание таблиц
    logger.info("\n[2/3] Creating database tables...")
    create_tables()
    logger.info("✓ Database tables created")

    # Шаг 3: Seeding (опционально)
    if seed:
        try:
            logger.info("\n[3/3] Seeding database with initial data...")
            logger.info("-" * 70)

            # Показываем статистику ДО seeding
            from core.database import SessionLocal
            from core.db_stats import log_table_statistics

            db = SessionLocal()
            try:
                log_table_statistics(db, title="Database State BEFORE Seeding")
            finally:
                db.close()

            # Запускаем seeding
            from scripts.seed_data import main as seed_main

            seed_main()

            # Показываем статистику ПОСЛЕ seeding
            db = SessionLocal()
            try:
                logger.info("")
                log_table_statistics(db, title="Database State AFTER Seeding")
            finally:
                db.close()

            logger.info("")
            logger.info("✓ Database seeding completed successfully")

        except Exception as e:
            logger.warning(f"⚠ Seeding failed (this is OK if data already exists)")
            logger.warning(f"  Error: {e}")
    else:
        logger.info("\n[3/3] Skipping database seeding (SEED_DATABASE=false)")

    logger.info("")
    logger.info("=" * 70)
    logger.info("✓ DATABASE INITIALIZATION COMPLETED".center(70))
    logger.info("=" * 70)
