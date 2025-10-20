"""
Security Headers Middleware.

Automatically adds security headers to all HTTP responses to protect against
common web vulnerabilities.

Implementation for User Story #46 - Security Headers Middleware (P1)
"""

import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.

    Headers added:
        - X-Content-Type-Options: Prevents MIME type sniffing
        - X-Frame-Options: Prevents clickjacking
        - X-XSS-Protection: Enables XSS filter in browsers
        - Strict-Transport-Security: Enforces HTTPS
        - Content-Security-Policy: Restricts resource loading
        - Referrer-Policy: Controls referrer information
        - Permissions-Policy: Controls browser features

    Configuration via environment variables:
        - SECURITY_HEADERS_ENABLED: Enable/disable middleware (default: True)
        - CSP_POLICY: Custom Content-Security-Policy (default: "default-src 'self'")
        - HSTS_MAX_AGE: HSTS max-age in seconds (default: 31536000 = 1 year)
        - FRAME_OPTIONS: X-Frame-Options value (default: DENY)

    Example:
        app.add_middleware(SecurityHeadersMiddleware)
    """

    def __init__(self, app):
        super().__init__(app)
        # Load configuration from environment
        self.enabled = os.getenv('SECURITY_HEADERS_ENABLED', 'true').lower() == 'true'
        self.csp_policy = os.getenv(
            'CSP_POLICY',
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        )
        self.hsts_max_age = int(os.getenv('HSTS_MAX_AGE', '31536000'))
        self.frame_options = os.getenv('FRAME_OPTIONS', 'DENY')

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response."""
        # Process request
        response = await call_next(request)

        # Skip if disabled
        if not self.enabled:
            return response

        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = self.frame_options
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Only add HSTS in production or if explicitly enabled
        if os.getenv('ENVIRONMENT') == 'production' or os.getenv('HSTS_ENABLED', 'false').lower() == 'true':
            response.headers['Strict-Transport-Security'] = f'max-age={self.hsts_max_age}; includeSubDomains; preload'

        # Content Security Policy
        response.headers['Content-Security-Policy'] = self.csp_policy

        # Referrer Policy - don't send referrer to other origins
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions Policy - restrict powerful features
        response.headers['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=()'
        )

        return response
