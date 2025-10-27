"""
Celery Application Configuration

Provides Celery task queue for background jobs like automated backups.

Implementation for User Story #27 - Automated Database Backup & Restore

Features:
    - Celery app initialization
    - Redis broker configuration
    - Task autodiscovery
    - Beat schedule for periodic tasks

Usage:
    # Start worker
    celery -A core.celery_app worker --loglevel=info

    # Start beat scheduler
    celery -A core.celery_app beat --loglevel=info
"""

import os
from celery import Celery
from celery.schedules import crontab

from core.config import get_settings

settings = get_settings()

# Create Celery app
app = Celery(
    "multipult",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["core.tasks"]
)

# Celery configuration
app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },

    # Broker settings
    broker_connection_retry_on_startup=True,

    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,

    # Beat schedule (for periodic tasks)
    beat_schedule={
        "daily-backup": {
            "task": "core.tasks.create_automated_backup",
            "schedule": crontab(hour=2, minute=0),  # Run at 2:00 AM daily
            "options": {
                "expires": 3600,
            }
        },
        "weekly-retention": {
            "task": "core.tasks.apply_backup_retention",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Run at 3:00 AM on Sundays
            "options": {
                "expires": 3600,
            }
        },
    },
)

if __name__ == "__main__":
    app.start()
