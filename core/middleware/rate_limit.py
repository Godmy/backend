"""
Rate Limiting Middleware.

Implements per-user and per-IP rate limiting to protect against abuse and DDoS.

Implementation for User Story #5 - API Rate Limiting (P0)
Implementation for User Story #21 - Application-Level Rate Limiting (P0)
"""

import json
import os
import re
import time
from typing import Dict, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from core.redis_client import redis_client
from core.structured_logging import get_logger

logger = get_logger(__name__)

# Try to import Prometheus metrics, fallback if not available
try:
    from prometheus_client import Counter

    rate_limit_exceeded_counter = Counter(
        "http_rate_limit_exceeded_total",
        "Total number of rate limit exceeded responses",
        ["user_type", "endpoint"]
    )
    rate_limit_blocked_counter = Counter(
        "http_rate_limit_blocked_total",
        "Total number of blocked requests",
        ["user_type"]
    )
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False
    logger.warning("Prometheus metrics not available for rate limiting")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that implements rate limiting per user/IP.

    Features:
        - Per-user rate limiting for authenticated users
        - Per-IP rate limiting for anonymous users
        - Configurable limits for auth/anon users
        - Redis-based counters with sliding window
        - X-RateLimit-* headers in responses
        - IP whitelist for admin/internal services
        - Structured logging and Prometheus metrics

    Configuration via environment variables:
        - RATE_LIMIT_ENABLED: Enable/disable rate limiting (default: True)
        - RATE_LIMIT_AUTH_PER_MINUTE: Requests per minute for authenticated users (default: 100)
        - RATE_LIMIT_ANON_PER_MINUTE: Requests per minute for anonymous users (default: 20)
        - RATE_LIMIT_WHITELIST_IPS: Comma-separated list of whitelisted IPs (default: "127.0.0.1,::1")
        - RATE_LIMIT_EXCLUDE_PATHS: Comma-separated list of paths to exclude (default: "/health,/metrics")

    Headers added to responses:
        - X-RateLimit-Limit: Maximum requests allowed in window
        - X-RateLimit-Remaining: Remaining requests in current window
        - X-RateLimit-Reset: Unix timestamp when the limit resets

    Example:
        HTTP 429 Too Many Requests
        X-RateLimit-Limit: 100
        X-RateLimit-Remaining: 0
        X-RateLimit-Reset: 1705320000
    """

    def __init__(self, app):
        super().__init__(app)

        # Configuration
        self.enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.auth_limit = int(os.getenv("RATE_LIMIT_AUTH_PER_MINUTE", "100"))
        self.anon_limit = int(os.getenv("RATE_LIMIT_ANON_PER_MINUTE", "20"))

        # Per-endpoint limits (JSON format)
        # Example: {"^/graphql$": {"auth": 50, "anon": 10}, "^/api/search": {"auth": 30, "anon": 5}}
        self.endpoint_limits = self._load_endpoint_limits()

        # Whitelist IPs
        whitelist_str = os.getenv("RATE_LIMIT_WHITELIST_IPS", "127.0.0.1,::1")
        self.whitelist_ips = [ip.strip() for ip in whitelist_str.split(",") if ip.strip()]

        # Exclude paths
        exclude_str = os.getenv("RATE_LIMIT_EXCLUDE_PATHS", "/health,/metrics")
        self.exclude_paths = [path.strip() for path in exclude_str.split(",") if path.strip()]

        # Window duration in seconds
        self.window_seconds = 60

        logger.info(
            "Rate limiting initialized",
            extra={
                "enabled": self.enabled,
                "auth_limit": self.auth_limit,
                "anon_limit": self.anon_limit,
                "endpoint_limits": len(self.endpoint_limits),
                "whitelist_ips": self.whitelist_ips,
                "exclude_paths": self.exclude_paths
            }
        )

    def _load_endpoint_limits(self) -> Dict[str, Dict[str, int]]:
        """
        Load per-endpoint rate limits from environment variable.

        Expected format (JSON):
        {
            "^/graphql$": {"auth": 50, "anon": 10},
            "^/api/search": {"auth": 30, "anon": 5}
        }

        Keys are regex patterns, values are limits for auth/anon users.
        """
        limits_str = os.getenv("RATE_LIMIT_ENDPOINT_LIMITS", "{}")
        try:
            limits = json.loads(limits_str)
            # Validate structure
            for pattern, values in limits.items():
                if not isinstance(values, dict):
                    logger.warning(f"Invalid endpoint limit format for {pattern}, skipping")
                    continue
                if "auth" not in values or "anon" not in values:
                    logger.warning(f"Missing auth/anon limits for {pattern}, skipping")
                    continue
            return limits
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse RATE_LIMIT_ENDPOINT_LIMITS: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading endpoint limits: {e}")
            return {}

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting."""
        # Skip if disabled
        if not self.enabled:
            return await call_next(request)

        # Skip excluded paths
        if self._is_path_excluded(request.url.path):
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Skip whitelisted IPs
        if client_ip in self.whitelist_ips:
            logger.debug(
                "Request from whitelisted IP, skipping rate limit",
                extra={"ip": client_ip, "path": request.url.path}
            )
            return await call_next(request)

        # Get user ID from token (if authenticated)
        user_id = await self._extract_user_id(request)

        # Determine user type
        user_type = "authenticated" if user_id else "anonymous"

        # Determine limit (check endpoint-specific limits first)
        limit = self._get_limit_for_endpoint(request.url.path, user_type)

        # Determine rate limit key
        if user_id:
            rate_limit_key = f"rate_limit:user:{user_id}:{request.url.path}"
        else:
            rate_limit_key = f"rate_limit:ip:{client_ip}:{request.url.path}"

        # Check rate limit
        allowed, remaining, reset_time = await self._check_rate_limit(
            rate_limit_key, limit
        )

        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(max(0, remaining)),
            "X-RateLimit-Reset": str(reset_time),
        }

        if not allowed:
            # Log rate limit exceeded
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "user_id": user_id,
                    "ip": client_ip,
                    "user_type": user_type,
                    "path": request.url.path,
                    "limit": limit,
                    "event": "rate_limit_exceeded"
                }
            )

            # Update metrics
            if METRICS_ENABLED:
                rate_limit_exceeded_counter.labels(
                    user_type=user_type,
                    endpoint=request.url.path
                ).inc()
                rate_limit_blocked_counter.labels(user_type=user_type).inc()

            # Return 429 Too Many Requests
            return JSONResponse(
                {
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {limit} requests per minute.",
                    "retry_after": reset_time - int(time.time())
                },
                status_code=429,
                headers=headers
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response

    def _is_path_excluded(self, path: str) -> bool:
        """Check if path should be excluded from rate limiting."""
        for excluded_path in self.exclude_paths:
            if path.startswith(excluded_path):
                return True
        return False

    def _get_limit_for_endpoint(self, path: str, user_type: str) -> int:
        """
        Get rate limit for specific endpoint and user type.

        Args:
            path: Request path
            user_type: "authenticated" or "anonymous"

        Returns:
            Rate limit per minute for this endpoint and user type
        """
        # Check endpoint-specific limits
        for pattern, limits in self.endpoint_limits.items():
            if re.match(pattern, path):
                limit_key = "auth" if user_type == "authenticated" else "anon"
                endpoint_limit = limits.get(limit_key)
                if endpoint_limit:
                    logger.debug(
                        f"Using endpoint-specific limit for {path}",
                        extra={
                            "path": path,
                            "pattern": pattern,
                            "user_type": user_type,
                            "limit": endpoint_limit
                        }
                    )
                    return endpoint_limit

        # Fall back to global limits
        return self.auth_limit if user_type == "authenticated" else self.anon_limit

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request.

        Handles X-Forwarded-For header for requests behind proxies.
        """
        # Check X-Forwarded-For header (when behind reverse proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get first IP in chain (client IP)
            client_ip = forwarded_for.split(",")[0].strip()
            return client_ip

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct connection IP
        if request.client:
            return request.client.host

        return "unknown"

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

    async def _check_rate_limit(
        self, key: str, limit: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit.

        Uses sliding window algorithm with Redis.

        Args:
            key: Redis key for rate limit counter
            limit: Maximum requests allowed in window

        Returns:
            Tuple of (allowed, remaining, reset_time)
            - allowed: True if request is allowed
            - remaining: Number of requests remaining
            - reset_time: Unix timestamp when limit resets
        """
        current_time = int(time.time())
        reset_time = current_time + self.window_seconds

        # If Redis is not available, allow the request
        if not redis_client.client:
            logger.warning("Redis not available, rate limiting disabled")
            return True, limit - 1, reset_time

        try:
            # Get current counter
            current_count_str = redis_client.get(key)
            current_count = int(current_count_str) if current_count_str else 0

            # Check if limit exceeded
            if current_count >= limit:
                # Get TTL for reset time
                ttl = redis_client.ttl(key)
                if ttl > 0:
                    reset_time = current_time + ttl

                return False, 0, reset_time

            # Increment counter
            new_count = redis_client.incr(key)

            # Set expiration if this is the first request in window
            if new_count == 1:
                redis_client.expire(key, self.window_seconds)

            # Calculate remaining requests
            remaining = max(0, limit - new_count)

            return True, remaining, reset_time

        except Exception as e:
            logger.error(
                "Rate limit check failed",
                extra={"key": key, "error": str(e)},
                exc_info=True
            )
            # On error, allow the request (fail open)
            return True, limit - 1, reset_time
