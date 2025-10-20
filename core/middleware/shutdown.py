"""
Shutdown Middleware.

Rejects new requests during graceful shutdown.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class ShutdownMiddleware(BaseHTTPMiddleware):
    """
    Middleware that rejects new requests during graceful shutdown.

    Returns 503 Service Unavailable when application is shutting down.
    """

    async def dispatch(self, request: Request, call_next):
        """Process request or reject if shutting down."""
        from core.shutdown import shutdown_handler

        # Check if application is shutting down
        if shutdown_handler.is_shutting_down():
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service Unavailable",
                    "message": "Application is shutting down, please try again later"
                }
            )

        # Process request normally
        return await call_next(request)
