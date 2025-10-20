"""
Prometheus metrics middleware.

Automatically collects HTTP request metrics (count, duration, in-progress).

User Story: #17 - Prometheus Metrics Collection (P0)
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_requests_in_progress
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic Prometheus metrics collection.

    Tracks:
    - Total HTTP requests (counter)
    - Request duration (histogram)
    - Requests in progress (gauge)

    Example:
        app.add_middleware(PrometheusMiddleware)
    """

    async def dispatch(self, request: Request, call_next):
        """Process request and collect metrics."""
        # Skip metrics collection for /metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        # Normalize endpoint path (remove IDs for better grouping)
        endpoint = self._normalize_path(request.url.path)
        method = request.method

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        # Measure request duration
        start_time = time.time()

        try:
            response: Response = await call_next(request)
            status = response.status_code
        except Exception as e:
            # Track failed requests
            status = 500
            raise e
        finally:
            # Record metrics
            duration = time.time() - start_time

            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()

            http_requests_in_progress.labels(
                method=method,
                endpoint=endpoint
            ).dec()

        return response

    @staticmethod
    def _normalize_path(path: str) -> str:
        """
        Normalize path for better metric grouping.

        Replaces numeric IDs with placeholders.

        Examples:
            /users/123 -> /users/{id}
            /concepts/456/translations -> /concepts/{id}/translations
        """
        # Known static paths
        static_paths = {
            "/graphql", "/health", "/health/detailed",
            "/metrics", "/uploads", "/docs", "/redoc"
        }

        if path in static_paths:
            return path

        # Replace numeric segments with {id}
        segments = path.split('/')
        normalized = []

        for segment in segments:
            if segment.isdigit():
                normalized.append('{id}')
            else:
                normalized.append(segment)

        return '/'.join(normalized)
