"""
Email sending tasks

Background tasks for asynchronous email delivery with retry logic.
"""

from typing import List, Optional, Union

from celery import Task
from core.celery_app import celery_app
from core.email_service import email_service
from core.structured_logging import get_logger

logger = get_logger(__name__)


class EmailTask(Task):
    """Base class for email tasks with custom error handling"""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 5}
    retry_backoff = True  # Enable exponential backoff
    retry_backoff_max = 600  # Max 10 minutes between retries
    retry_jitter = True  # Add randomness to prevent thundering herd


@celery_app.task(
    bind=True,
    base=EmailTask,
    name="tasks.send_email",
    queue="default",
)
def send_email_task(
    self,
    to_email: Union[str, List[str]],
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    reply_to: Optional[str] = None,
    request_id: Optional[str] = None,
):
    """
    Send email task with retry logic

    Args:
        to_email: Recipient email address or list of addresses
        subject: Email subject
        html_content: HTML version of the email
        text_content: Plain text version (optional)
        reply_to: Reply-To email address (optional)
        request_id: Request ID for tracing (optional)

    Returns:
        bool: True if email sent successfully

    Raises:
        Exception: If email sending fails after all retries
    """
    try:
        logger.info(
            f"Sending email to {to_email}: {subject}",
            extra={"request_id": request_id, "task_id": self.request.id},
        )

        success = email_service.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            reply_to=reply_to,
        )

        if not success:
            raise Exception("Email service returned failure")

        logger.info(
            f"Email sent successfully to {to_email}",
            extra={"request_id": request_id, "task_id": self.request.id},
        )
        return True

    except Exception as exc:
        logger.error(
            f"Failed to send email to {to_email}: {exc}",
            extra={
                "request_id": request_id,
                "task_id": self.request.id,
                "retry": self.request.retries,
            },
        )
        raise


@celery_app.task(
    bind=True,
    base=EmailTask,
    name="tasks.send_verification_email",
    queue="default",
)
def send_verification_email_task(
    self,
    to_email: str,
    username: str,
    token: str,
    request_id: Optional[str] = None,
):
    """
    Send email verification link

    Args:
        to_email: Recipient email
        username: User's username
        token: Verification token
        request_id: Request ID for tracing (optional)

    Returns:
        bool: True if sent successfully

    Raises:
        Exception: If email sending fails after all retries
    """
    try:
        logger.info(
            f"Sending verification email to {to_email}",
            extra={"request_id": request_id, "task_id": self.request.id},
        )

        success = email_service.send_verification_email(
            to_email=to_email,
            username=username,
            token=token,
        )

        if not success:
            raise Exception("Email service returned failure")

        logger.info(
            f"Verification email sent to {to_email}",
            extra={"request_id": request_id, "task_id": self.request.id},
        )
        return True

    except Exception as exc:
        logger.error(
            f"Failed to send verification email to {to_email}: {exc}",
            extra={
                "request_id": request_id,
                "task_id": self.request.id,
                "retry": self.request.retries,
            },
        )
        raise


@celery_app.task(
    bind=True,
    base=EmailTask,
    name="tasks.send_password_reset_email",
    queue="default",
)
def send_password_reset_email_task(
    self,
    to_email: str,
    username: str,
    token: str,
    request_id: Optional[str] = None,
):
    """
    Send password reset link

    Args:
        to_email: Recipient email
        username: User's username
        token: Password reset token
        request_id: Request ID for tracing (optional)

    Returns:
        bool: True if sent successfully

    Raises:
        Exception: If email sending fails after all retries
    """
    try:
        logger.info(
            f"Sending password reset email to {to_email}",
            extra={"request_id": request_id, "task_id": self.request.id},
        )

        success = email_service.send_password_reset_email(
            to_email=to_email,
            username=username,
            token=token,
        )

        if not success:
            raise Exception("Email service returned failure")

        logger.info(
            f"Password reset email sent to {to_email}",
            extra={"request_id": request_id, "task_id": self.request.id},
        )
        return True

    except Exception as exc:
        logger.error(
            f"Failed to send password reset email to {to_email}: {exc}",
            extra={
                "request_id": request_id,
                "task_id": self.request.id,
                "retry": self.request.retries,
            },
        )
        raise


@celery_app.task(
    bind=True,
    base=EmailTask,
    name="tasks.send_welcome_email",
    queue="default",
)
def send_welcome_email_task(
    self,
    to_email: str,
    username: str,
    request_id: Optional[str] = None,
):
    """
    Send welcome email to new user

    Args:
        to_email: Recipient email
        username: User's username
        request_id: Request ID for tracing (optional)

    Returns:
        bool: True if sent successfully

    Raises:
        Exception: If email sending fails after all retries
    """
    try:
        logger.info(
            f"Sending welcome email to {to_email}",
            extra={"request_id": request_id, "task_id": self.request.id},
        )

        success = email_service.send_welcome_email(
            to_email=to_email,
            username=username,
        )

        if not success:
            raise Exception("Email service returned failure")

        logger.info(
            f"Welcome email sent to {to_email}",
            extra={"request_id": request_id, "task_id": self.request.id},
        )
        return True

    except Exception as exc:
        logger.error(
            f"Failed to send welcome email to {to_email}: {exc}",
            extra={
                "request_id": request_id,
                "task_id": self.request.id,
                "retry": self.request.retries,
            },
        )
        raise
