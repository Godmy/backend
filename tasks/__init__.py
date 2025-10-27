"""
Background tasks module

Contains Celery task implementations for:
- Email sending
- File processing (thumbnails, cleanup)
- Periodic tasks
"""

from tasks.email_tasks import (
    send_email_task,
    send_verification_email_task,
    send_password_reset_email_task,
    send_welcome_email_task,
)
from tasks.file_tasks import (
    generate_thumbnail_task,
    cleanup_old_files_task,
    cleanup_temporary_files_task,
)
from tasks.periodic_tasks import (
    periodic_file_cleanup_task,
    periodic_health_check_task,
)

__all__ = [
    # Email tasks
    "send_email_task",
    "send_verification_email_task",
    "send_password_reset_email_task",
    "send_welcome_email_task",
    # File tasks
    "generate_thumbnail_task",
    "cleanup_old_files_task",
    "cleanup_temporary_files_task",
    # Periodic tasks
    "periodic_file_cleanup_task",
    "periodic_health_check_task",
]
