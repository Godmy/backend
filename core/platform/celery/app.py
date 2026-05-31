from __future__ import annotations

import os

from celery import Celery
from kombu import Exchange, Queue


def _redis_url() -> str:
    if os.getenv("CELERY_BROKER_URL"):
        return os.getenv("CELERY_BROKER_URL", "")

    host = os.getenv("REDIS_HOST", "redis")
    port = os.getenv("REDIS_PORT", "6379")
    db = os.getenv("REDIS_DB", "0")
    password = os.getenv("REDIS_PASSWORD", "")

    if password:
        return f"redis://:{password}@{host}:{port}/{db}"
    return f"redis://{host}:{port}/{db}"


celery_app = Celery("vibe_management_backend")
celery_app.conf.update(
    broker_url=_redis_url(),
    result_backend=os.getenv("CELERY_RESULT_BACKEND", _redis_url()),
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone=os.getenv("CELERY_TIMEZONE", "UTC"),
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=int(os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "1")),
    task_default_queue="default",
    task_default_exchange="default",
    task_default_exchange_type="direct",
    task_default_routing_key="default",
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("low_priority", Exchange("low_priority"), routing_key="low_priority"),
    ),
)
