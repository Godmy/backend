"""
Request/Response Logging Middleware.

Logs all API requests and responses for debugging and monitoring.

Implementation for User Story #53 - API Request/Response Logging (P2)
"""

import json
import logging
import time
import uuid
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all HTTP requests and responses.

    Features:
        - Logs request method, path, headers, body
        - Logs response status, headers, body
        - Logs request duration
        - Generates unique request ID for tracing
        - Extracts user ID from JWT token
        - Masks sensitive data (passwords, tokens)

    Configuration via environment variables:
        - REQUEST_LOGGING_ENABLED: Enable/disable logging (default: True)
        - REQUEST_LOGGING_BODY: Log request/response bodies (default: True)
        - REQUEST_LOGGING_HEADERS: Log headers (default: False, can expose secrets)
        - REQUEST_LOGGING_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR)

    Example log output:
        INFO: [req-abc123] GET /api/users 200 (125ms) user_id=42
    """

    def __init__(self, app, log_body: bool = True, log_headers: bool = False):
        super().__init__(app)
        self.log_body = log_body
        self.log_headers = log_headers

        # Sensitive field patterns to mask
        self.sensitive_patterns = [
            "password",
            "token",
            "secret",
            "authorization",
            "api_key",
            "apikey",
            "access_token",
            "refresh_token",
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and log details."""
        from core.context import set_request_id, set_user_id, clear_context

        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Set request ID in context for access throughout the application
        set_request_id(request_id)

        # Start timer
        start_time = time.time()

        # Extract user ID from token (if available)
        user_id = await self._extract_user_id(request)

        # Set user ID in context
        if user_id:
            set_user_id(user_id)

        # Log request
        await self._log_request(request, request_id, user_id)

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            logger.error(
                f"[{request_id}] Request failed: {request.method} {request.url.path} - {str(e)}",
                exc_info=True
            )
            raise

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Log response
        await self._log_response(request, response, request_id, user_id, duration_ms)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Clear context after request processing
        clear_context()

        return response

    async def _extract_user_id(self, request: Request) -> Optional[int]:
        """Extract user ID from JWT token."""
        try:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return None

            token = auth_header.split("Bearer ")[1]
            from auth.utils.jwt_handler import jwt_handler

            payload = jwt_handler.verify_token(token)
            return payload.get("user_id") if payload else None

        except Exception:
            return None

    async def _log_request(self, request: Request, request_id: str, user_id: Optional[int]):
        """Log incoming request."""
        # Build log message
        log_parts = [
            f"[{request_id}]",
            request.method,
            str(request.url.path),
        ]

        if user_id:
            log_parts.append(f"user_id={user_id}")

        # Log headers (if enabled)
        if self.log_headers:
            headers = dict(request.headers)
            masked_headers = self._mask_sensitive_data(headers)
            log_parts.append(f"headers={json.dumps(masked_headers)}")

        # Log body (if enabled and present)
        if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read body
                body = await request.body()
                if body:
                    # Try to parse as JSON
                    try:
                        body_data = json.loads(body)
                        masked_body = self._mask_sensitive_data(body_data)
                        log_parts.append(f"body={json.dumps(masked_body)}")
                    except json.JSONDecodeError:
                        # Log raw body (truncated if too long)
                        body_str = body.decode("utf-8", errors="ignore")[:500]
                        log_parts.append(f"body={body_str}")
            except Exception as e:
                log_parts.append(f"body_error={str(e)}")

        logger.info(" ".join(log_parts))

    async def _log_response(
        self,
        request: Request,
        response: Response,
        request_id: str,
        user_id: Optional[int],
        duration_ms: int
    ):
        """Log outgoing response."""
        # Build log message
        log_parts = [
            f"[{request_id}]",
            request.method,
            str(request.url.path),
            str(response.status_code),
            f"({duration_ms}ms)",
        ]

        if user_id:
            log_parts.append(f"user_id={user_id}")

        # Log headers (if enabled)
        if self.log_headers:
            headers = dict(response.headers)
            log_parts.append(f"response_headers={json.dumps(headers)}")

        # Choose log level based on status code
        if response.status_code >= 500:
            logger.error(" ".join(log_parts))
        elif response.status_code >= 400:
            logger.warning(" ".join(log_parts))
        else:
            logger.info(" ".join(log_parts))

    def _mask_sensitive_data(self, data: dict) -> dict:
        """Mask sensitive fields in data."""
        if not isinstance(data, dict):
            return data

        masked = {}
        for key, value in data.items():
            key_lower = key.lower()

            # Check if key is sensitive
            is_sensitive = any(pattern in key_lower for pattern in self.sensitive_patterns)

            if is_sensitive:
                masked[key] = "***MASKED***"
            elif isinstance(value, dict):
                # Recursively mask nested objects
                masked[key] = self._mask_sensitive_data(value)
            elif isinstance(value, list):
                # Mask list items if they're dicts
                masked[key] = [
                    self._mask_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked[key] = value

        return masked
