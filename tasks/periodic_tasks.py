"""
Periodic tasks configuration

Defines scheduled tasks to run at regular intervals using Celery Beat.
"""

import os
from datetime import timedelta
from typing import Optional

from celery import Task
from celery.schedules import crontab
from core.celery_app import celery_app
from core.structured_logging import get_logger
from tasks.file_tasks import cleanup_temporary_files_task, cleanup_old_files_task

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="tasks.periodic_file_cleanup",
    queue="low_priority",
)
def periodic_file_cleanup_task(self):
    """
    Periodic task to clean up old and temporary files

    Runs daily to:
    - Clean temporary files older than 1 day
    - Clean old uploads older than 90 days (configurable)

    Returns:
        dict: Cleanup statistics
    """
    try:
        logger.info(
            "Running periodic file cleanup",
            extra={"task_id": self.request.id},
        )

        results = {
            "temp_cleanup": {},
            "old_files_cleanup": {},
        }

        # Clean temporary files (older than 1 day)
        results["temp_cleanup"] = cleanup_temporary_files_task()

        # Clean old files from uploads directory
        upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        max_age_days = int(os.getenv("FILE_CLEANUP_MAX_AGE_DAYS", "90"))

        if os.path.exists(upload_dir):
            results["old_files_cleanup"] = cleanup_old_files_task(
                directory=upload_dir,
                max_age_days=max_age_days,
            )

        logger.info(
            "Periodic file cleanup completed",
            extra={
                "task_id": self.request.id,
                "results": results,
            },
        )

        return results

    except Exception as exc:
        logger.error(
            f"Periodic file cleanup failed: {exc}",
            extra={"task_id": self.request.id},
        )
        return {"success": False, "error": str(exc)}


@celery_app.task(
    bind=True,
    name="tasks.periodic_health_check",
    queue="low_priority",
)
def periodic_health_check_task(self):
    """
    Periodic health check task

    Runs every hour to verify system health and log status.

    Returns:
        dict: Health check results
    """
    try:
        logger.info(
            "Running periodic health check",
            extra={"task_id": self.request.id},
        )

        # Import here to avoid circular dependencies
        from core.database import engine
        from core.redis_client import redis_client
        from sqlalchemy import text

        health_status = {
            "database": False,
            "redis": False,
            "celery": True,  # If this task is running, Celery is healthy
        }

        # Check database connection
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            health_status["database"] = True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")

        # Check Redis connection
        try:
            redis_client.ping()
            health_status["redis"] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")

        # Log overall health status
        all_healthy = all(health_status.values())
        log_level = "info" if all_healthy else "warning"
        logger.log(
            level=log_level,
            msg=f"Health check completed: {'healthy' if all_healthy else 'degraded'}",
            extra={
                "task_id": self.request.id,
                "health_status": health_status,
            },
        )

        return {
            "success": True,
            "healthy": all_healthy,
            "checks": health_status,
        }

    except Exception as exc:
        logger.error(
            f"Health check task failed: {exc}",
            extra={"task_id": self.request.id},
        )
        return {"success": False, "error": str(exc)}


# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    # Clean up temporary files daily at 2 AM
    "cleanup-temporary-files": {
        "task": "tasks.periodic_file_cleanup",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "low_priority"},
    },
    # Health check every hour
    "health-check": {
        "task": "tasks.periodic_health_check",
        "schedule": timedelta(hours=1),
        "options": {"queue": "low_priority"},
    },
}

logger.info("Periodic tasks schedule configured")
