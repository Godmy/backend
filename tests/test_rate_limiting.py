"""
Tests for Rate Limiting Middleware.

Tests rate limiting functionality for authenticated and anonymous users.
"""

import os
import time
from unittest.mock import MagicMock, patch

import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from auth.utils.jwt_handler import jwt_handler
from core.middleware.rate_limit import RateLimitMiddleware
from core.redis_client import redis_client


@pytest.fixture
def rate_limit_app():
    """Create test app with rate limiting middleware."""

    async def test_endpoint(request):
        return JSONResponse({"status": "ok"})

    app = Starlette(
        routes=[
            Route("/api/test", test_endpoint),
            Route("/health", test_endpoint),
        ]
    )

    # Add rate limiting with test configuration
    with patch.dict(
        os.environ,
        {
            "RATE_LIMIT_ENABLED": "true",
            "RATE_LIMIT_AUTH_PER_MINUTE": "5",  # Low limit for testing
            "RATE_LIMIT_ANON_PER_MINUTE": "2",  # Very low limit for testing
            "RATE_LIMIT_WHITELIST_IPS": "192.168.1.100",
            "RATE_LIMIT_EXCLUDE_PATHS": "/health",
        },
    ):
        app.add_middleware(RateLimitMiddleware)

    return app


@pytest.fixture
def client(rate_limit_app):
    """Create test client."""
    return TestClient(rate_limit_app)


@pytest.fixture
def auth_token(db):
    """Create authentication token for testing."""
    token_data = {"sub": "testuser", "user_id": 999, "email": "test@example.com"}
    return jwt_handler.create_access_token(token_data)


@pytest.fixture(autouse=True)
def cleanup_redis():
    """Clean up Redis keys after each test."""
    yield
    # Clean up rate limit keys
    if redis_client.client:
        keys = redis_client.keys("rate_limit:*")
        for key in keys:
            redis_client.delete(key)


def test_rate_limit_anonymous_within_limit(client):
    """Test that anonymous requests within limit are allowed."""
    # Make 2 requests (within limit of 2 per minute)
    response1 = client.get("/api/test")
    response2 = client.get("/api/test")

    assert response1.status_code == 200
    assert response2.status_code == 200

    # Check rate limit headers
    assert "X-RateLimit-Limit" in response1.headers
    assert response1.headers["X-RateLimit-Limit"] == "2"
    assert response1.headers["X-RateLimit-Remaining"] == "1"

    assert response2.headers["X-RateLimit-Remaining"] == "0"


def test_rate_limit_anonymous_exceeds_limit(client):
    """Test that anonymous requests exceeding limit are blocked."""
    # Make requests up to limit
    for _ in range(2):
        response = client.get("/api/test")
        assert response.status_code == 200

    # Next request should be rate limited
    response = client.get("/api/test")
    assert response.status_code == 429
    assert "error" in response.json()
    assert "Rate limit exceeded" in response.json()["error"]

    # Check headers
    assert response.headers["X-RateLimit-Limit"] == "2"
    assert response.headers["X-RateLimit-Remaining"] == "0"


def test_rate_limit_authenticated_within_limit(client, auth_token):
    """Test that authenticated requests within limit are allowed."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Make 5 requests (within limit of 5 per minute)
    for i in range(5):
        response = client.get("/api/test", headers=headers)
        assert response.status_code == 200
        assert int(response.headers["X-RateLimit-Remaining"]) == 4 - i


def test_rate_limit_authenticated_exceeds_limit(client, auth_token):
    """Test that authenticated requests exceeding limit are blocked."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Make requests up to limit
    for _ in range(5):
        response = client.get("/api/test", headers=headers)
        assert response.status_code == 200

    # Next request should be rate limited
    response = client.get("/api/test", headers=headers)
    assert response.status_code == 429
    assert "error" in response.json()
    assert response.headers["X-RateLimit-Limit"] == "5"


def test_rate_limit_different_users_separate_counters(client, db):
    """Test that different users have separate rate limit counters."""
    # Create tokens for two different users
    token1_data = {"sub": "user1", "user_id": 100, "email": "user1@example.com"}
    token2_data = {"sub": "user2", "user_id": 200, "email": "user2@example.com"}

    token1 = jwt_handler.create_access_token(token1_data)
    token2 = jwt_handler.create_access_token(token2_data)

    # User 1 makes 5 requests (hits limit)
    for _ in range(5):
        response = client.get("/api/test", headers={"Authorization": f"Bearer {token1}"})
        assert response.status_code == 200

    # User 1 is now rate limited
    response = client.get("/api/test", headers={"Authorization": f"Bearer {token1}"})
    assert response.status_code == 429

    # User 2 should still be able to make requests
    response = client.get("/api/test", headers={"Authorization": f"Bearer {token2}"})
    assert response.status_code == 200


def test_rate_limit_whitelisted_ip_bypasses_limit(client):
    """Test that whitelisted IPs bypass rate limiting."""
    # Make requests from whitelisted IP
    for _ in range(10):  # Way more than limit
        response = client.get(
            "/api/test", headers={"X-Forwarded-For": "192.168.1.100"}
        )
        assert response.status_code == 200


def test_rate_limit_excluded_path_bypasses_limit(client):
    """Test that excluded paths bypass rate limiting."""
    # Make many requests to /health endpoint
    for _ in range(100):  # Way more than any limit
        response = client.get("/health")
        assert response.status_code == 200


def test_rate_limit_headers_present(client):
    """Test that rate limit headers are always present."""
    response = client.get("/api/test")

    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers

    # Check that values are valid
    assert int(response.headers["X-RateLimit-Limit"]) > 0
    assert int(response.headers["X-RateLimit-Remaining"]) >= 0
    assert int(response.headers["X-RateLimit-Reset"]) > int(time.time())


def test_rate_limit_reset_after_window(client):
    """Test that rate limit resets after time window."""
    # Make requests up to limit
    for _ in range(2):
        response = client.get("/api/test")
        assert response.status_code == 200

    # Next request should be rate limited
    response = client.get("/api/test")
    assert response.status_code == 429

    # Wait for window to expire (using Redis directly for testing)
    if redis_client.client:
        # Get the key
        keys = redis_client.keys("rate_limit:ip:*")
        if keys:
            # Set TTL to 0 to simulate window expiry
            redis_client.delete(keys[0])

    # Request should now succeed
    response = client.get("/api/test")
    assert response.status_code == 200


def test_rate_limit_disabled(rate_limit_app):
    """Test that rate limiting can be disabled."""
    with patch.dict(os.environ, {"RATE_LIMIT_ENABLED": "false"}):
        # Recreate app with disabled rate limiting
        async def test_endpoint(request):
            return JSONResponse({"status": "ok"})

        app = Starlette(routes=[Route("/api/test", test_endpoint)])
        app.add_middleware(RateLimitMiddleware)
        client = TestClient(app)

        # Make many requests - all should succeed
        for _ in range(100):
            response = client.get("/api/test")
            assert response.status_code == 200


def test_rate_limit_redis_unavailable_fails_open(client):
    """Test that when Redis is unavailable, requests are allowed (fail open)."""
    # Mock Redis client to be unavailable
    with patch.object(redis_client, "client", None):
        # Requests should still succeed
        for _ in range(10):
            response = client.get("/api/test")
            assert response.status_code == 200


def test_rate_limit_x_forwarded_for_header(client):
    """Test that X-Forwarded-For header is used for IP extraction."""
    # Make requests with X-Forwarded-For header
    headers = {"X-Forwarded-For": "203.0.113.195, 70.41.3.18, 150.172.238.178"}

    # First IP in chain should be used
    for _ in range(2):
        response = client.get("/api/test", headers=headers)
        assert response.status_code == 200

    # Rate limit should apply to that IP
    response = client.get("/api/test", headers=headers)
    assert response.status_code == 429


def test_rate_limit_retry_after_header(client):
    """Test that retry_after is included in 429 response."""
    # Exceed rate limit
    for _ in range(2):
        client.get("/api/test")

    response = client.get("/api/test")
    assert response.status_code == 429

    # Check retry_after in response body
    data = response.json()
    assert "retry_after" in data
    assert isinstance(data["retry_after"], int)
    assert data["retry_after"] > 0


def test_rate_limit_per_endpoint_limits():
    """Test that different endpoints can have different rate limits."""
    import json

    # Create app with per-endpoint limits
    async def test_endpoint(request):
        return JSONResponse({"status": "ok"})

    async def graphql_endpoint(request):
        return JSONResponse({"data": {}})

    async def search_endpoint(request):
        return JSONResponse({"results": []})

    app = Starlette(
        routes=[
            Route("/api/test", test_endpoint),
            Route("/graphql", graphql_endpoint),
            Route("/api/search", search_endpoint),
        ]
    )

    # Configure per-endpoint limits
    endpoint_limits = {
        "^/graphql$": {"auth": 3, "anon": 1},  # Very restrictive for graphql
        "^/api/search": {"auth": 5, "anon": 2},  # Moderate for search
    }

    with patch.dict(
        os.environ,
        {
            "RATE_LIMIT_ENABLED": "true",
            "RATE_LIMIT_AUTH_PER_MINUTE": "10",  # Global default
            "RATE_LIMIT_ANON_PER_MINUTE": "5",  # Global default
            "RATE_LIMIT_ENDPOINT_LIMITS": json.dumps(endpoint_limits),
        },
    ):
        app.add_middleware(RateLimitMiddleware)

    client = TestClient(app)

    # Test /graphql endpoint (limit: 1 for anon)
    response1 = client.get("/graphql")
    assert response1.status_code == 200
    assert response1.headers["X-RateLimit-Limit"] == "1"

    # Second request should be rate limited
    response2 = client.get("/graphql")
    assert response2.status_code == 429

    # Test /api/search endpoint (limit: 2 for anon)
    for _ in range(2):
        response = client.get("/api/search")
        assert response.status_code == 200
        assert response.headers["X-RateLimit-Limit"] == "2"

    # Third request should be rate limited
    response = client.get("/api/search")
    assert response.status_code == 429

    # Test /api/test endpoint (uses global limit: 5 for anon)
    for _ in range(5):
        response = client.get("/api/test")
        assert response.status_code == 200
        assert response.headers["X-RateLimit-Limit"] == "5"

    # Sixth request should be rate limited
    response = client.get("/api/test")
    assert response.status_code == 429


def test_rate_limit_per_endpoint_auth_users():
    """Test that authenticated users get different limits per endpoint."""
    import json

    async def graphql_endpoint(request):
        return JSONResponse({"data": {}})

    app = Starlette(routes=[Route("/graphql", graphql_endpoint)])

    endpoint_limits = {
        "^/graphql$": {"auth": 3, "anon": 1},
    }

    with patch.dict(
        os.environ,
        {
            "RATE_LIMIT_ENABLED": "true",
            "RATE_LIMIT_AUTH_PER_MINUTE": "10",
            "RATE_LIMIT_ANON_PER_MINUTE": "5",
            "RATE_LIMIT_ENDPOINT_LIMITS": json.dumps(endpoint_limits),
        },
    ):
        app.add_middleware(RateLimitMiddleware)

    client = TestClient(app)

    # Create auth token
    token_data = {"sub": "testuser", "user_id": 999, "email": "test@example.com"}
    token = jwt_handler.create_access_token(token_data)
    headers = {"Authorization": f"Bearer {token}"}

    # Authenticated user should have limit of 3
    for i in range(3):
        response = client.get("/graphql", headers=headers)
        assert response.status_code == 200
        assert response.headers["X-RateLimit-Limit"] == "3"
        assert int(response.headers["X-RateLimit-Remaining"]) == 2 - i

    # Fourth request should be rate limited
    response = client.get("/graphql", headers=headers)
    assert response.status_code == 429


def test_rate_limit_per_endpoint_regex_patterns():
    """Test that regex patterns work for matching endpoints."""
    import json

    async def api_endpoint(request):
        return JSONResponse({"status": "ok"})

    app = Starlette(
        routes=[
            Route("/api/users", api_endpoint),
            Route("/api/users/123", api_endpoint),
            Route("/api/posts", api_endpoint),
        ]
    )

    endpoint_limits = {
        "^/api/users": {"auth": 2, "anon": 1},  # Matches /api/users*
    }

    with patch.dict(
        os.environ,
        {
            "RATE_LIMIT_ENABLED": "true",
            "RATE_LIMIT_AUTH_PER_MINUTE": "10",
            "RATE_LIMIT_ANON_PER_MINUTE": "5",
            "RATE_LIMIT_ENDPOINT_LIMITS": json.dumps(endpoint_limits),
        },
    ):
        app.add_middleware(RateLimitMiddleware)

    client = TestClient(app)

    # /api/users should match pattern (limit: 1)
    response = client.get("/api/users")
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "1"

    response = client.get("/api/users")
    assert response.status_code == 429

    # /api/users/123 should also match pattern (limit: 1)
    response = client.get("/api/users/123")
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "1"

    # /api/posts should NOT match pattern, use global limit (5)
    response = client.get("/api/posts")
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "5"
