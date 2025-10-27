"""
Celery Context Middleware

Propagates request context (request_id, user_id) to Celery tasks.
This allows for distributed tracing across HTTP requests and background tasks.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from core.context import get_request_id
from core.structured_logging import get_logger

logger = get_logger(__name__)


class CeleryContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to capture request context for Celery tasks

    This middleware doesn't modify the request/response directly,
    but makes request_id available for task invocations within the request.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request and make context available for task calls

        The request_id is already set by RequestLoggingMiddleware,
        so we just need to ensure it's available when tasks are called.
        """
        # Request ID is already in context from RequestLoggingMiddleware
        request_id = get_request_id()

        # Store in request state for easy access
        request.state.celery_context = {
            "request_id": request_id,
        }

        # Continue processing
        response = await call_next(request)
        return response


def get_celery_context(request: Request = None) -> dict:
    """
    Get Celery context from current request

    Args:
        request: Current request object (optional)

    Returns:
        dict: Context to pass to Celery tasks (includes request_id)
    """
    if request and hasattr(request.state, "celery_context"):
        return request.state.celery_context

    # Fallback: get request_id from context
    return {
        "request_id": get_request_id(),
    }
