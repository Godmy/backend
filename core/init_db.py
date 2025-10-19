"""
Модуль инициализации базы данных
Отвечает за ожидание подключения к БД, создание таблиц и регистрацию всех моделей
"""
import time
import logging
from sqlalchemy import text, exc

from core.database import engine, Base

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
                    f"Database not ready, retrying in {delay}s... "
                    f"({i+1}/{max_retries})"
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"Could not connect to database after {max_retries} retries: {e}"
                )
                raise
    return False


def import_all_models():
    """
    Импортирует все модели, чтобы они зарегистрировались в Base.metadata
    Это необходимо для корректного создания таблиц
    """
    # Импортируем модели из модуля auth (ПЕРВЫМИ, т.к. на них ссылаются другие модели)
    from auth.models import user, role, permission, profile, oauth

    # Импортируем модели из core
    from core.models import file, audit_log

    # Импортируем модели из модуля languages
    from languages.models import language, concept, dictionary

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
    wait_for_db()
    create_tables()

    if seed:
        try:
            logger.info("Seeding database with test data...")
            from scripts.seed_data import main as seed_main
            seed_main()
        except Exception as e:
            logger.warning(f"Seeding failed (this is OK if data already exists): {e}")

    logger.info("Database initialization completed")
