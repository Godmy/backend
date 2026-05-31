from __future__ import annotations

from importlib import import_module
import os
import time

from sqlalchemy import text

from core.platform.db.database import Base, engine
from core.platform.logging.structured_logging import get_logger


logger = get_logger(__name__)


def import_all_models() -> None:
    import auth.models  # noqa: F401
    import core.models  # noqa: F401
    import languages.models  # noqa: F401


def create_tables() -> None:
    import_all_models()
    Base.metadata.create_all(bind=engine)


def wait_for_db(max_attempts: int = 20, delay_seconds: float = 1.5) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Database connection established")
            return
        except Exception as exc:
            if attempt == max_attempts:
                raise
            logger.warning(
                "Database is not ready yet (attempt %s/%s): %s",
                attempt,
                max_attempts,
                exc,
            )
            time.sleep(delay_seconds)


def _default_init_database() -> None:
    wait_for_db()
    create_tables()

    if os.getenv("SEED_DATABASE", "false").lower() == "true":
        logger.info("SEED_DATABASE is enabled, but automatic seeding is not wired here")


def _load_backend_init_hook():
    try:
        module = import_module("backend.hooks.database")
    except ModuleNotFoundError:
        return None
    return getattr(module, "init_database", None)


def init_database(stage: str = "app", original=None) -> None:
    def base_initializer(*args, **kwargs) -> None:
        _default_init_database()

        if callable(original):
            try:
                original(*args, **kwargs)
            except TypeError:
                original()

    backend_init_hook = _load_backend_init_hook()
    if callable(backend_init_hook):
        backend_init_hook(stage=stage, original=base_initializer)
        return

    base_initializer(stage=stage)
