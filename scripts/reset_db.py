"""
Полный сброс dev-базы данных: удаляет всю схему `public` (все таблицы, все
данные), пересоздаёт её по текущим SQLAlchemy-моделям (create_tables()) и
прогоняет сидеры заново.

Только для dev-окружения — отказывается работать при ENVIRONMENT=production.
Обходится без Alembic намеренно: в dev нет истории данных, которую нужно
сохранять при правке моделей, поэтому проще пересоздать схему с нуля, чем
писать/чинить миграцию на каждое изменение (см. packages/.claude/skills/db-tables).

Использование:
    python scripts/reset_db.py --yes
    python scripts/reset_db.py --yes --skip-seed
    python scripts/reset_db.py --yes --seeders languages roles users
"""

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from core.platform.config import get_settings
from core.platform.db.database import SessionLocal, engine
from core.platform.db.init_db import create_tables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(
        description="DESTRUCTIVE: drops every table and all data, then rebuilds schema + seed data. Dev-only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full reset: drop everything, rebuild schema, run all seeders
  python scripts/reset_db.py --yes

  # Rebuild schema only, seed manually later
  python scripts/reset_db.py --yes --skip-seed

  # Reset and run only specific seeders
  python scripts/reset_db.py --yes --seeders languages roles users
        """,
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required confirmation flag. The script refuses to run without it.",
    )
    parser.add_argument(
        "--seeders",
        nargs="+",
        help="Run only these seeders after rebuilding the schema (default: all).",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Rebuild the schema only, skip running seeders.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_arguments(argv)
    settings = get_settings()

    if settings.environment == "production":
        logger.error("Refusing to run: ENVIRONMENT=production. This script is dev-only.")
        return 1

    if not args.yes:
        target = settings.database_url.rsplit("@", 1)[-1]
        logger.error(
            "This drops every table and all data in '%s'. Re-run with --yes to confirm.",
            target,
        )
        return 1

    logger.warning("Dropping schema 'public' (all tables, all data)...")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()

    logger.info("Recreating tables from current models...")
    create_tables()

    # Дренаж создаёт схему заново из текущих моделей (= HEAD), а не через
    # историю миграций — если БД когда-либо отслеживалась Alembic'ом,
    # синхронизируем метку версии, чтобы будущие миграции применялись поверх.
    try:
        from alembic import command
        from alembic.config import Config

        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_cfg = Config(os.path.join(backend_root, "alembic.ini"))
        command.stamp(alembic_cfg, "head")
        logger.info("Stamped Alembic revision at head")
    except Exception as exc:
        logger.warning("Could not stamp Alembic revision (non-fatal): %s", exc)

    if args.skip_seed:
        logger.info("Schema rebuilt, seeding skipped (--skip-seed)")
        return 0

    logger.info("Seeding database...")
    from scripts.seeders.orchestrator import SeederOrchestrator

    db = SessionLocal()
    try:
        orchestrator = SeederOrchestrator(db)
        if args.seeders:
            results = orchestrator.run_specific(args.seeders)
        else:
            results = orchestrator.run_all(skip_if_exists=True)
    finally:
        db.close()

    failed = [result.name for result in results if result.status == "failed"]
    if failed:
        logger.error("Seeding completed with failures: %s", ", ".join(failed))
        return 1

    logger.info("Database reset and seeded successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
