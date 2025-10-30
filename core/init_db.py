"""
Database bootstrap helpers.

Utilities to wait for the database, create tables, and optionally seed
initial data so local and CI environments start in a consistent state.
"""

import logging
import time

from sqlalchemy import exc, text

from core.database import Base, engine

logger = logging.getLogger(__name__)


def wait_for_db(max_retries: int = 30, delay: int = 2) -> bool:
    """Poll the database until a connection succeeds."""
    for attempt in range(max_retries):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except exc.OperationalError as error:
            if attempt < max_retries - 1:
                logger.warning(
                    "Database not ready, retrying in %ss... (%s/%s)",
                    delay,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(delay)
            else:
                logger.error(
                    "Could not connect to database after %s retries: %s",
                    max_retries,
                    error,
                )
                raise
    return False


def import_all_models() -> None:
    """Import all model modules so SQLAlchemy metadata is populated."""
    from auth.models import oauth, permission, profile, role, user
    from core.models import audit_log, file
    from languages.models import concept, dictionary, language

    logger.info("Imported SQLAlchemy models for auth, core, and languages")


def create_tables() -> None:
    """Create any missing tables defined on Base.metadata."""
    try:
        logger.info("Creating database tables...")
        import_all_models()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as error:  # pylint: disable=broad-except
        logger.error("Error creating tables: %s", error)
        raise


def _log_table_stats(title: str) -> None:
    """Helper to log database statistics when available."""
    try:
        from core.database import SessionLocal
        from core.db_stats import log_table_statistics

        db = SessionLocal()
        try:
            log_table_statistics(db, title=title)
        finally:
            db.close()
    except Exception as error:  # pylint: disable=broad-except
        logger.debug("Could not log table statistics (%s): %s", title, error)


def init_database(seed: bool = True) -> None:
    """Initialise the database: connectivity, tables, optional seeding."""
    logger.info("=" * 70)
    logger.info("DATABASE INITIALIZATION".center(70))
    logger.info("=" * 70)

    logger.info("\n[1/3] Waiting for database connection...")
    wait_for_db()
    logger.info("[OK] Database connection established")

    logger.info("\n[2/3] Creating database tables...")
    create_tables()
    logger.info("[OK] Database tables created")

    if seed:
        logger.info("\n[3/3] Seeding database with initial data...")
        logger.info("-" * 70)
        _log_table_stats(title="Database State BEFORE Seeding")

        try:
            from scripts.seed_data import main as seed_main

            exit_code = seed_main([])
            if exit_code != 0:
                logger.warning("Database seeding script exited with code %s", exit_code)
            else:
                _log_table_stats(title="Database State AFTER Seeding")
                logger.info("Database seeding completed successfully")
        except Exception as error:  # pylint: disable=broad-except
            logger.warning("Seeding failed (this is OK if data already exists)")
            logger.warning("  Error: %s", error)
    else:
        logger.info("\n[3/3] Skipping database seeding (SEED_DATABASE=false)")

    logger.info("")
    logger.info("=" * 70)
    logger.info("DATABASE INITIALIZATION COMPLETED".center(70))
    logger.info("=" * 70)
