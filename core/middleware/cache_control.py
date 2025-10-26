"""
HTTP Caching Headers Middleware.

Implements Cache-Control, ETag generation, and conditional requests (304 Not Modified)
to reduce server load and improve response times.

Implementation for User Story #22 - HTTP Caching Headers Middleware (P0)
"""

import hashlib
import json
import os
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.structured_logging import get_logger

logger = get_logger(__name__)

# Try to import Prometheus metrics
try:
    from prometheus_client import Counter

    cache_hits_counter = Counter(
        "http_cache_hits_total",
        "Total number of HTTP cache hits (304 responses)",
        ["endpoint"]
    )
    cache_misses_counter = Counter(
        "http_cache_misses_total",
        "Total number of HTTP cache misses",
        ["endpoint"]
    )
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False
    logger.warning("Prometheus metrics not available for cache control")


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds HTTP caching headers and handles conditional requests.

    Features:
        - Cache-Control headers based on endpoint type
        - ETag generation for responses
        - Conditional requests (If-None-Match)
        - 304 Not Modified responses
        - Configurable cache policies
        - Automatic no-cache for mutations
        - Prometheus metrics for cache hits/misses

    Configuration via environment variables:
        - CACHE_CONTROL_ENABLED: Enable/disable cache control (default: True)
        - CACHE_CONTROL_QUERY_MAX_AGE: Max age for queries in seconds (default: 60)
        - CACHE_CONTROL_DEFAULT_MAX_AGE: Max age for other endpoints (default: 30)
        - CACHE_CONTROL_EXCLUDE_PATHS: Comma-separated paths to exclude (default: "/metrics")

    Headers added:
        - Cache-Control: Caching directives
        - ETag: Response hash for cache validation
        - Vary: Authorization (for authenticated responses)

    Example:
        app.add_middleware(CacheControlMiddleware)
    """

    def __init__(self, app):
        super().__init__(app)

        # Configuration
        self.enabled = os.getenv("CACHE_CONTROL_ENABLED", "true").lower() == "true"
        self.query_max_age = int(os.getenv("CACHE_CONTROL_QUERY_MAX_AGE", "60"))
        self.default_max_age = int(os.getenv("CACHE_CONTROL_DEFAULT_MAX_AGE", "30"))

        # Exclude paths from caching
        exclude_str = os.getenv("CACHE_CONTROL_EXCLUDE_PATHS", "/metrics")
        self.exclude_paths = [path.strip() for path in exclude_str.split(",") if path.strip()]

        logger.info(
            "Cache control middleware initialized",
            extra={
                "enabled": self.enabled,
                "query_max_age": self.query_max_age,
                "default_max_age": self.default_max_age,
                "exclude_paths": self.exclude_paths
            }
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add cache headers to response."""
        # Skip if disabled
        if not self.enabled:
            return await call_next(request)

        # Skip excluded paths
        if self._is_path_excluded(request.url.path):
            return await call_next(request)

        # For GraphQL, need to check if it's query or mutation
        is_graphql = request.url.path == "/graphql"
        is_mutation = False

        if is_graphql and request.method == "POST":
            # Read body to detect mutations
            body = await request.body()
            is_mutation = await self._is_graphql_mutation(body)

            # Reconstruct request with body (since we read it)
            async def receive():
                return {"type": "http.request", "body": body}

            request._receive = receive

        # Process request
        response = await call_next(request)

        # Don't cache error responses
        if response.status_code >= 400:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response

        # Determine cache policy
        cache_control = self._get_cache_control(
            path=request.url.path,
            is_graphql=is_graphql,
            is_mutation=is_mutation,
            has_auth=request.headers.get("Authorization") is not None
        )

        response.headers["Cache-Control"] = cache_control

        # Add Vary header for authenticated responses
        if request.headers.get("Authorization"):
            response.headers["Vary"] = "Authorization"

        # Generate ETag if cacheable (not for mutations or no-cache)
        if "no-cache" not in cache_control and "no-store" not in cache_control:
            # Read response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # Generate ETag
            etag = self._generate_etag(response_body)
            response.headers["ETag"] = f'"{etag}"'

            # Check If-None-Match for conditional requests
            client_etag = request.headers.get("If-None-Match")
            if client_etag and client_etag.strip('"') == etag:
                # Cache hit - return 304 Not Modified
                logger.debug(
                    "Cache hit - returning 304 Not Modified",
                    extra={
                        "path": request.url.path,
                        "etag": etag,
                        "event": "cache_hit"
                    }
                )

                # Update metrics
                if METRICS_ENABLED:
                    cache_hits_counter.labels(endpoint=request.url.path).inc()

                # Return 304 with minimal headers
                return Response(
                    status_code=304,
                    headers={
                        "Cache-Control": cache_control,
                        "ETag": f'"{etag}"',
                    }
                )

            # Cache miss
            if METRICS_ENABLED:
                cache_misses_counter.labels(endpoint=request.url.path).inc()

            # Reconstruct response with body
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

        return response

    def _is_path_excluded(self, path: str) -> bool:
        """Check if path should be excluded from cache control."""
        for excluded_path in self.exclude_paths:
            if path.startswith(excluded_path):
                return True
        return False

    async def _is_graphql_mutation(self, body: bytes) -> bool:
        """
        Detect if GraphQL request is a mutation.

        Args:
            body: Request body bytes

        Returns:
            True if request contains mutation, False otherwise
        """
        try:
            # Parse JSON body
            body_str = body.decode("utf-8")
            data = json.loads(body_str)

            # Check query field
            query = data.get("query", "")
            if not query:
                return False

            # Simple heuristic: check if query starts with "mutation"
            # Remove whitespace and comments
            query_clean = query.strip().lower()
            return query_clean.startswith("mutation")

        except Exception as e:
            logger.debug(f"Failed to parse GraphQL body: {e}")
            # If we can't parse, assume it's not cacheable
            return True

    def _get_cache_control(
        self,
        path: str,
        is_graphql: bool = False,
        is_mutation: bool = False,
        has_auth: bool = False
    ) -> str:
        """
        Determine Cache-Control header value.

        Args:
            path: Request path
            is_graphql: True if GraphQL request
            is_mutation: True if GraphQL mutation
            has_auth: True if request has Authorization header

        Returns:
            Cache-Control header value
        """
        # No cache for mutations
        if is_mutation:
            return "no-cache, no-store, must-revalidate"

        # GraphQL queries - cacheable
        if is_graphql:
            if has_auth:
                return f"private, max-age={self.query_max_age}"
            else:
                return f"public, max-age={self.query_max_age}"

        # Health check - no cache
        if path.startswith("/health"):
            return "no-cache"

        # Default caching
        if has_auth:
            return f"private, max-age={self.default_max_age}"
        else:
            return f"public, max-age={self.default_max_age}"

    def _generate_etag(self, content: bytes) -> str:
        """
        Generate ETag from response content.

        Args:
            content: Response body bytes

        Returns:
            ETag value (MD5 hash)
        """
        return hashlib.md5(content).hexdigest()
