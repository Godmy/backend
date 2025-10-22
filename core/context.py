"""
Request Context Management.

Provides context variables for tracking request_id across the application,
including HTTP handlers, GraphQL resolvers, background tasks, and database operations.

Implementation for User Story #20 - Request ID & Distributed Tracing (P0)
"""

from contextvars import ContextVar
from typing import Optional
import uuid

# Context variable for request ID (thread-safe)
request_id_ctx: ContextVar[Optional[str]] = ContextVar('request_id', default=None)

# Context variable for user ID (for logging)
user_id_ctx: ContextVar[Optional[int]] = ContextVar('user_id', default=None)


def get_request_id() -> str:
    """
    Get current request ID from context.

    Returns:
        Request ID (UUID) or generates new one if not set

    Example:
        from core.context import get_request_id

        request_id = get_request_id()
        logger.info(f"Processing request {request_id}")
    """
    rid = request_id_ctx.get()
    if rid is None:
        # Generate new request ID if not set (e.g., in background tasks)
        rid = str(uuid.uuid4())[:8]
        request_id_ctx.set(rid)
    return rid


def set_request_id(request_id: str) -> None:
    """
    Set request ID in context.

    Args:
        request_id: Request ID to set

    Example:
        from core.context import set_request_id

        set_request_id("abc12345")
    """
    request_id_ctx.set(request_id)


def get_user_id() -> Optional[int]:
    """
    Get current user ID from context.

    Returns:
        User ID or None if not authenticated

    Example:
        from core.context import get_user_id

        user_id = get_user_id()
        if user_id:
            logger.info(f"Request from user {user_id}")
    """
    return user_id_ctx.get()


def set_user_id(user_id: Optional[int]) -> None:
    """
    Set user ID in context.

    Args:
        user_id: User ID to set

    Example:
        from core.context import set_user_id

        set_user_id(123)
    """
    user_id_ctx.set(user_id)


def clear_context() -> None:
    """
    Clear all context variables.

    Should be called after request processing is complete.
    """
    request_id_ctx.set(None)
    user_id_ctx.set(None)


class RequestContextFilter:
    """
    Logging filter that adds request_id and user_id to log records.

    Usage:
        import logging
        from core.context import RequestContextFilter

        logger = logging.getLogger(__name__)
        logger.addFilter(RequestContextFilter())

        # Now all logs will include request_id and user_id
        logger.info("Processing request")
        # Output: [abc12345] [user:123] Processing request
    """

    def filter(self, record):
        """Add request_id and user_id to log record."""
        # Get from context, use defaults if not available
        request_id = request_id_ctx.get()
        user_id = user_id_ctx.get()

        record.request_id = request_id if request_id else "-"
        record.user_id = user_id if user_id else "-"
        return True
