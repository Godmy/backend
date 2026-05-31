from __future__ import annotations

from typing import List, Optional, Union

from celery import Task

from core.platform.celery.app import celery_app
from core.platform.email.email_service import email_service
from core.platform.logging.structured_logging import get_logger


logger = get_logger(__name__)


class EmailTask(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 5}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


@celery_app.task(bind=True, base=EmailTask, name="tasks.send_email", queue="default")
def send_email_task(
    self,
    to_email: Union[str, List[str]],
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    reply_to: Optional[str] = None,
    request_id: Optional[str] = None,
):
    try:
        logger.info(
            "Sending email to %s: %s",
            to_email,
            subject,
            extra={"request_id": request_id, "task_id": self.request.id},
        )

        success = email_service.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            reply_to=reply_to,
            idempotency_key=self.request.id,
        )
        if not success:
            raise Exception("Email service returned failure")

        logger.info(
            "Email sent successfully to %s",
            to_email,
            extra={"request_id": request_id, "task_id": self.request.id},
        )
        return True
    except Exception as exc:
        logger.error(
            "Failed to send email to %s: %s",
            to_email,
            exc,
            extra={
                "request_id": request_id,
                "task_id": self.request.id,
                "retry": self.request.retries,
            },
        )
        raise


@celery_app.task(bind=True, base=EmailTask, name="tasks.send_verification_email", queue="default")
def send_verification_email_task(
    self,
    to_email: str,
    username: str,
    token: str,
    request_id: Optional[str] = None,
):
    try:
        logger.info(
            "Sending verification email to %s",
            to_email,
            extra={"request_id": request_id, "task_id": self.request.id},
        )

        success = email_service.send_verification_email(
            to_email=to_email,
            username=username,
            token=token,
            idempotency_key=self.request.id,
        )
        if not success:
            raise Exception("Email service returned failure")

        logger.info(
            "Verification email sent to %s",
            to_email,
            extra={"request_id": request_id, "task_id": self.request.id},
        )
        return True
    except Exception as exc:
        logger.error(
            "Failed to send verification email to %s: %s",
            to_email,
            exc,
            extra={
                "request_id": request_id,
                "task_id": self.request.id,
                "retry": self.request.retries,
            },
        )
        raise


@celery_app.task(bind=True, base=EmailTask, name="tasks.send_password_reset_email", queue="default")
def send_password_reset_email_task(
    self,
    to_email: str,
    username: str,
    token: str,
    request_id: Optional[str] = None,
):
    try:
        logger.info(
            "Sending password reset email to %s",
            to_email,
            extra={"request_id": request_id, "task_id": self.request.id},
        )

        success = email_service.send_password_reset_email(
            to_email=to_email,
            username=username,
            token=token,
            idempotency_key=self.request.id,
        )
        if not success:
            raise Exception("Email service returned failure")

        logger.info(
            "Password reset email sent to %s",
            to_email,
            extra={"request_id": request_id, "task_id": self.request.id},
        )
        return True
    except Exception as exc:
        logger.error(
            "Failed to send password reset email to %s: %s",
            to_email,
            exc,
            extra={
                "request_id": request_id,
                "task_id": self.request.id,
                "retry": self.request.retries,
            },
        )
        raise


@celery_app.task(bind=True, base=EmailTask, name="tasks.send_welcome_email", queue="default")
def send_welcome_email_task(
    self,
    to_email: str,
    username: str,
    request_id: Optional[str] = None,
):
    try:
        logger.info(
            "Sending welcome email to %s",
            to_email,
            extra={"request_id": request_id, "task_id": self.request.id},
        )

        success = email_service.send_welcome_email(
            to_email=to_email,
            username=username,
            idempotency_key=self.request.id,
        )
        if not success:
            raise Exception("Email service returned failure")

        logger.info(
            "Welcome email sent to %s",
            to_email,
            extra={"request_id": request_id, "task_id": self.request.id},
        )
        return True
    except Exception as exc:
        logger.error(
            "Failed to send welcome email to %s: %s",
            to_email,
            exc,
            extra={
                "request_id": request_id,
                "task_id": self.request.id,
                "retry": self.request.retries,
            },
        )
        raise
