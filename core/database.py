from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import settings
from core.structured_logging import get_logger

logger = get_logger(__name__)

# Get validated database configuration
DATABASE_URL = settings.database_url

logger.info(f"Connecting to database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

# Создаем движок с настройками для PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,  # Normal pool size (was 50 due to connection leak)
    max_overflow=20,  # Normal overflow (was 50 due to connection leak)
    echo=False,
    connect_args={"connect_timeout": 10, "application_name": "attractors_app"},
)

# Setup query profiling (after engine creation)
# This will automatically log queries in DEBUG mode and monitor slow queries
try:
    from core.services.query_profiler import setup_query_profiling
    setup_query_profiling(
        engine,
        enabled=True,
        slow_query_threshold_ms=100,
        log_all_queries=settings.DEBUG
    )
except ImportError:
    logger.warning("Query profiler not available, skipping query profiling setup")
except Exception as e:
    logger.error(f"Failed to setup query profiling: {e}", exc_info=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

# Создаем базовый класс для моделей
Base = declarative_base()


# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(
            "Database session error",
            extra={"error": str(e), "error_type": type(e).__name__, "event": "db_session_error"},
            exc_info=True
        )
        db.rollback()
        raise
    finally:
        db.close()
