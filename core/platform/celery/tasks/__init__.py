from .email import (
    send_email_task,
    send_password_reset_email_task,
    send_verification_email_task,
    send_welcome_email_task,
)
from .files import (
    cleanup_old_files_task,
    cleanup_temporary_files_task,
    generate_thumbnail_task,
)
from .periodic import periodic_file_cleanup_task, periodic_health_check_task


def register_tasks() -> None:
    # Import side effects register tasks with Celery.
    return None


__all__ = [
    "register_tasks",
    "send_email_task",
    "send_verification_email_task",
    "send_password_reset_email_task",
    "send_welcome_email_task",
    "generate_thumbnail_task",
    "cleanup_old_files_task",
    "cleanup_temporary_files_task",
    "periodic_file_cleanup_task",
    "periodic_health_check_task",
]
