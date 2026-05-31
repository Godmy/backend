from __future__ import annotations

from core.platform.celery.app import celery_app
from core.platform.celery.tasks import register_tasks
from core.platform.logging.structured_logging import get_logger, setup_logging


setup_logging()
register_tasks()

logger = get_logger(__name__)
logger.info("Celery worker starting...")
logger.info("Registered tasks: %s", list(celery_app.tasks.keys()))

app = celery_app


if __name__ == "__main__":
    logger.info("Starting Celery worker via Python...")
    celery_app.start()
