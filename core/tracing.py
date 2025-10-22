"""
Distributed Tracing Utilities.

Provides helpers for propagating request_id across async tasks,
database queries, and external service calls.

Implementation for User Story #20 - Request ID & Distributed Tracing (P0)
"""

import functools
import logging
from typing import Callable, Any
from core.context import get_request_id, set_request_id, get_user_id, set_user_id

logger = logging.getLogger(__name__)


def with_request_context(func: Callable) -> Callable:
    """
    Decorator that propagates request context to async functions.

    Useful for background tasks, celery tasks, or any async operation
    that needs access to request_id and user_id.

    Example:
        from core.tracing import with_request_context

        @with_request_context
        async def send_email_task(user_id: int, email: str):
            # request_id is automatically available in logs
            logger.info(f"Sending email to {email}")

        # Call from request handler
        await send_email_task(user.id, user.email)
    """

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Capture current context
        request_id = get_request_id()
        user_id = get_user_id()

        # Log task start
        logger.info(f"Starting async task: {func.__name__}")

        try:
            # Execute function (context is inherited)
            result = await func(*args, **kwargs)
            logger.info(f"Completed async task: {func.__name__}")
            return result
        except Exception as e:
            logger.error(
                f"Error in async task {func.__name__}: {str(e)}",
                exc_info=True
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        # Capture current context
        request_id = get_request_id()
        user_id = get_user_id()

        # Log task start
        logger.info(f"Starting sync task: {func.__name__}")

        try:
            # Execute function (context is inherited)
            result = func(*args, **kwargs)
            logger.info(f"Completed sync task: {func.__name__}")
            return result
        except Exception as e:
            logger.error(
                f"Error in sync task {func.__name__}: {str(e)}",
                exc_info=True
            )
            raise

    # Return appropriate wrapper based on function type
    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def celery_task_with_context(request_id: str = None, user_id: int = None):
    """
    Decorator for Celery tasks that sets request context.

    Since Celery tasks run in separate processes, we need to explicitly
    pass and restore the request context.

    Example:
        from celery import shared_task
        from core.tracing import celery_task_with_context
        from core.context import get_request_id

        @shared_task
        @celery_task_with_context()
        def send_email(to_email: str, subject: str, request_id: str = None, user_id: int = None):
            # request_id is now available in logs
            logger.info(f"Sending email to {to_email}")

        # Call from request handler
        request_id = get_request_id()
        user_id = get_user_id()
        send_email.delay(
            to_email="user@example.com",
            subject="Welcome",
            request_id=request_id,
            user_id=user_id
        )
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract context from kwargs
            rid = kwargs.pop('request_id', None)
            uid = kwargs.pop('user_id', None)

            # Set context for this task
            if rid:
                set_request_id(rid)
            if uid:
                set_user_id(uid)

            logger.info(f"Starting Celery task: {func.__name__}")

            try:
                result = func(*args, **kwargs)
                logger.info(f"Completed Celery task: {func.__name__}")
                return result
            except Exception as e:
                logger.error(
                    f"Error in Celery task {func.__name__}: {str(e)}",
                    exc_info=True
                )
                raise

        return wrapper

    return decorator


class TracingHelper:
    """
    Helper class for manual tracing instrumentation.

    Use when you need fine-grained control over tracing spans.

    Example:
        from core.tracing import TracingHelper

        def process_order(order_id: int):
            with TracingHelper.span("process_order") as span:
                span.set_tag("order_id", order_id)

                # Do work
                validate_order(order_id)
                span.log("Order validated")

                charge_payment(order_id)
                span.log("Payment charged")

                fulfill_order(order_id)
                span.log("Order fulfilled")
    """

    class Span:
        """Simple span implementation for logging."""

        def __init__(self, name: str):
            self.name = name
            self.tags = {}
            self.request_id = get_request_id()
            self.user_id = get_user_id()

        def __enter__(self):
            logger.info(f"Starting span: {self.name}")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type:
                logger.error(
                    f"Span {self.name} failed: {exc_val}",
                    exc_info=(exc_type, exc_val, exc_tb)
                )
            else:
                logger.info(f"Completed span: {self.name}")

        def set_tag(self, key: str, value: Any):
            """Set a tag on the span."""
            self.tags[key] = value
            logger.debug(f"Span {self.name} tag: {key}={value}")

        def log(self, message: str):
            """Log a message within the span."""
            logger.info(f"Span {self.name}: {message}")

    @classmethod
    def span(cls, name: str) -> 'TracingHelper.Span':
        """
        Create a new tracing span.

        Args:
            name: Name of the span (e.g., "db_query", "api_call")

        Returns:
            Span context manager
        """
        return cls.Span(name)
