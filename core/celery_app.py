"""
Celery application instance and configuration

This module sets up Celery with Redis broker for background task processing.
Includes retry logic, dead letter queue, and integration with structured logging.
"""

import os
from celery import Celery
from celery.signals import (
    task_prerun,
    task_postrun,
    task_failure,
    task_retry,
    task_success,
)
from kombu import Queue, Exchange

from core.structured_logging import get_logger

logger = get_logger(__name__)

# Get Redis configuration from environment
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Construct Redis URL for Celery broker
if REDIS_PASSWORD:
    CELERY_BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
else:
    CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Use Redis as result backend as well
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# Create Celery app instance
celery_app = Celery(
    "multipult",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

# Dead letter exchange and queue for failed tasks
dead_letter_exchange = Exchange("dead_letter", type="topic", durable=True)
dead_letter_queue = Queue(
    "dead_letter",
    exchange=dead_letter_exchange,
    routing_key="dead_letter.#",
    durable=True,
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task result settings
    result_expires=3600,  # 1 hour
    result_persistent=True,

    # Task execution
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
    task_track_started=True,  # Track task started state

    # Worker settings
    worker_prefetch_multiplier=1,  # Fetch one task at a time
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    worker_disable_rate_limits=False,

    # Retry settings
    task_publish_retry=True,
    task_publish_retry_policy={
        "max_retries": 3,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.2,
    },

    # Task routing and queues
    task_queues=(
        Queue("default", routing_key="task.#", durable=True),
        Queue("high_priority", routing_key="priority.high.#", durable=True),
        Queue("low_priority", routing_key="priority.low.#", durable=True),
        dead_letter_queue,
    ),
    task_default_queue="default",
    task_default_exchange="tasks",
    task_default_exchange_type="topic",
    task_default_routing_key="task.default",

    # Beat schedule (for periodic tasks)
    beat_schedule={},  # Will be populated by task modules

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Auto-discover tasks from registered modules
celery_app.autodiscover_tasks([
    "tasks.email_tasks",
    "tasks.file_tasks",
    "tasks.periodic_tasks",
])


# Signal handlers for logging and monitoring
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """Log task start"""
    request_id = kwargs.get("request_id") if kwargs else None
    logger.info(
        f"Task started: {task.name}",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "request_id": request_id,
        },
    )


@task_postrun.connect
def task_postrun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **extra
):
    """Log task completion"""
    request_id = kwargs.get("request_id") if kwargs else None
    logger.info(
        f"Task finished: {task.name}",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "state": state,
            "request_id": request_id,
        },
    )


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Log successful task completion"""
    logger.debug(f"Task succeeded: {sender.name}", extra={"task_name": sender.name})


@task_failure.connect
def task_failure_handler(
    sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **extra
):
    """Log task failure"""
    request_id = kwargs.get("request_id") if kwargs else None
    logger.error(
        f"Task failed: {sender.name}",
        extra={
            "task_id": task_id,
            "task_name": sender.name,
            "exception": str(exception),
            "request_id": request_id,
        },
        exc_info=einfo,
    )


@task_retry.connect
def task_retry_handler(
    sender=None, task_id=None, reason=None, einfo=None, args=None, kwargs=None, **extra
):
    """Log task retry"""
    request_id = kwargs.get("request_id") if kwargs else None
    logger.warning(
        f"Task retry: {sender.name}",
        extra={
            "task_id": task_id,
            "task_name": sender.name,
            "reason": str(reason),
            "request_id": request_id,
        },
    )


# Helper function to get request context
def get_task_context():
    """
    Get current task context including request_id

    This can be called from within tasks to access the propagated request context.
    """
    from celery import current_task

    if current_task and current_task.request:
        return {
            "task_id": current_task.request.id,
            "task_name": current_task.name,
            "retries": current_task.request.retries,
        }
    return {}
