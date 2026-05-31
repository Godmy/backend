from __future__ import annotations

import logging
import os
from datetime import timedelta

from celery.schedules import crontab

from core.platform.celery.app import celery_app
from core.platform.celery.tasks.files import cleanup_old_files_task, cleanup_temporary_files_task
from core.platform.logging.structured_logging import get_logger


logger = get_logger(__name__)


@celery_app.task(bind=True, name="tasks.periodic_file_cleanup", queue="low_priority")
def periodic_file_cleanup_task(self):
    try:
        logger.info("Running periodic file cleanup", extra={"task_id": self.request.id})

        results = {
            "temp_cleanup": cleanup_temporary_files_task(),
            "old_files_cleanup": {},
        }

        upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        max_age_days = int(os.getenv("FILE_CLEANUP_MAX_AGE_DAYS", "90"))
        if os.path.exists(upload_dir):
            results["old_files_cleanup"] = cleanup_old_files_task(
                directory=upload_dir,
                max_age_days=max_age_days,
            )

        logger.info(
            "Periodic file cleanup completed",
            extra={"task_id": self.request.id, "results": results},
        )
        return results
    except Exception as exc:
        logger.error(
            "Periodic file cleanup failed: %s",
            exc,
            extra={"task_id": self.request.id},
        )
        return {"success": False, "error": str(exc)}


@celery_app.task(bind=True, name="tasks.periodic_health_check", queue="low_priority")
def periodic_health_check_task(self):
    try:
        logger.info("Running periodic health check", extra={"task_id": self.request.id})

        from sqlalchemy import text

        from core.platform.db.database import engine
        from core.platform.redis.client import redis_client

        health_status = {
            "database": False,
            "redis": False,
            "celery": True,
        }

        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            health_status["database"] = True
        except Exception as exc:
            logger.error("Database health check failed: %s", exc)

        try:
            redis_client.ping()
            health_status["redis"] = True
        except Exception as exc:
            logger.error("Redis health check failed: %s", exc)

        all_healthy = all(health_status.values())
        logger.log(
            level=logging.INFO if all_healthy else logging.WARNING,
            msg="Health check completed: %s" % ("healthy" if all_healthy else "degraded"),
            extra={"task_id": self.request.id, "health_status": health_status},
        )
        return {
            "success": True,
            "healthy": all_healthy,
            "checks": health_status,
        }
    except Exception as exc:
        logger.error(
            "Health check task failed: %s",
            exc,
            extra={"task_id": self.request.id},
        )
        return {"success": False, "error": str(exc)}


celery_app.conf.beat_schedule = {
    "cleanup-temporary-files": {
        "task": "tasks.periodic_file_cleanup",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "low_priority"},
    },
    "health-check": {
        "task": "tasks.periodic_health_check",
        "schedule": timedelta(hours=1),
        "options": {"queue": "low_priority"},
    },
}

