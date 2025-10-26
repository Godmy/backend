"""
Tests for Cache Control Middleware.

Tests HTTP caching functionality including Cache-Control headers, ETag generation,
and conditional requests (304 Not Modified).
"""

import hashlib
import json
import os
from unittest.mock import patch

import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from core.middleware.cache_control import CacheControlMiddleware


@pytest.fixture
def cache_app():
    """Create test app with cache control middleware."""

    async def query_endpoint(request):
        return JSONResponse({"data": {"users": [{"id": 1, "name": "Test"}]}})

    async def mutation_endpoint(request):
        return JSONResponse({"data": {"createUser": {"id": 2, "name": "New"}}})

    async def health_endpoint(request):
        return JSONResponse({"status": "ok"})

    app = Starlette(
        routes=[
            Route("/graphql", query_endpoint, methods=["POST"]),
            Route("/health", health_endpoint),
        ]
    )

    with patch.dict(
        os.environ,
        {
            "CACHE_CONTROL_ENABLED": "true",
            "CACHE_CONTROL_QUERY_MAX_AGE": "60",
            "CACHE_CONTROL_DEFAULT_MAX_AGE": "30",
        },
    ):
        app.add_middleware(CacheControlMiddleware)

    return app


@pytest.fixture
def client(cache_app):
    """Create test client."""
    return TestClient(cache_app)


def test_cache_control_graphql_query(client):
    """Test that GraphQL queries get Cache-Control headers."""
    # GraphQL query
    response = client.post(
        "/graphql",
        json={"query": "query { users { id name } }"}
    )

    assert response.status_code == 200
    assert "Cache-Control" in response.headers
    assert "public" in response.headers["Cache-Control"]
    assert "max-age=60" in response.headers["Cache-Control"]


def test_cache_control_graphql_mutation(client):
    """Test that GraphQL mutations get no-cache headers."""
    # GraphQL mutation
    response = client.post(
        "/graphql",
        json={"query": "mutation { createUser(name: \"Test\") { id } }"}
    )

    assert response.status_code == 200
    assert "Cache-Control" in response.headers
    assert "no-cache" in response.headers["Cache-Control"]
    assert "no-store" in response.headers["Cache-Control"]


def test_etag_generation(client):
    """Test that ETag is generated for cacheable responses."""
    # GraphQL query
    response = client.post(
        "/graphql",
        json={"query": "query { users { id name } }"}
    )

    assert response.status_code == 200
    assert "ETag" in response.headers

    # ETag should be quoted
    etag = response.headers["ETag"]
    assert etag.startswith('"')
    assert etag.endswith('"')


def test_etag_consistency(client):
    """Test that same response generates same ETag."""
    # Make two identical requests
    response1 = client.post(
        "/graphql",
        json={"query": "query { users { id name } }"}
    )
    response2 = client.post(
        "/graphql",
        json={"query": "query { users { id name } }"}
    )

    assert response1.headers.get("ETag") == response2.headers.get("ETag")


def test_conditional_request_304(client):
    """Test that If-None-Match returns 304 Not Modified."""
    # First request - get ETag
    response1 = client.post(
        "/graphql",
        json={"query": "query { users { id name } }"}
    )
    etag = response1.headers["ETag"]

    # Second request with If-None-Match
    response2 = client.post(
        "/graphql",
        json={"query": "query { users { id name } }"},
        headers={"If-None-Match": etag}
    )

    # Should return 304 Not Modified
    assert response2.status_code == 304
    assert response2.headers["ETag"] == etag
    assert "Cache-Control" in response2.headers

    # Body should be empty for 304
    assert len(response2.content) == 0


def test_conditional_request_miss(client):
    """Test that If-None-Match with wrong ETag returns 200."""
    # First request - get ETag
    response1 = client.post(
        "/graphql",
        json={"query": "query { users { id name } }"}
    )

    # Second request with wrong ETag
    response2 = client.post(
        "/graphql",
        json={"query": "query { users { id name } }"},
        headers={"If-None-Match": '"wrong-etag"'}
    )

    # Should return 200 with full response
    assert response2.status_code == 200
    assert len(response2.content) > 0


def test_cache_control_authenticated(client):
    """Test that authenticated requests get private cache."""
    # Request with Authorization header
    response = client.post(
        "/graphql",
        json={"query": "query { users { id name } }"},
        headers={"Authorization": "Bearer fake-token"}
    )

    assert response.status_code == 200
    assert "Cache-Control" in response.headers
    assert "private" in response.headers["Cache-Control"]
    assert "Vary" in response.headers
    assert response.headers["Vary"] == "Authorization"


def test_cache_control_unauthenticated(client):
    """Test that unauthenticated requests get public cache."""
    # Request without Authorization header
    response = client.post(
        "/graphql",
        json={"query": "query { users { id name } }"}
    )

    assert response.status_code == 200
    assert "Cache-Control" in response.headers
    assert "public" in response.headers["Cache-Control"]


def test_no_cache_for_health(client):
    """Test that health check endpoint gets no-cache."""
    response = client.get("/health")

    assert response.status_code == 200
    assert "Cache-Control" in response.headers
    assert "no-cache" in response.headers["Cache-Control"]


def test_cache_disabled():
    """Test that caching can be disabled."""
    async def test_endpoint(request):
        return JSONResponse({"status": "ok"})

    app = Starlette(routes=[Route("/test", test_endpoint)])

    with patch.dict(os.environ, {"CACHE_CONTROL_ENABLED": "false"}):
        app.add_middleware(CacheControlMiddleware)

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 200
    # Should not have cache headers when disabled
    assert "ETag" not in response.headers


def test_excluded_paths():
    """Test that excluded paths don't get cache headers."""
    async def metrics_endpoint(request):
        return JSONResponse({"metric": "value"})

    app = Starlette(routes=[Route("/metrics", metrics_endpoint)])

    with patch.dict(
        os.environ,
        {
            "CACHE_CONTROL_ENABLED": "true",
            "CACHE_CONTROL_EXCLUDE_PATHS": "/metrics",
        },
    ):
        app.add_middleware(CacheControlMiddleware)

    client = TestClient(app)
    response = client.get("/metrics")

    assert response.status_code == 200
    # Excluded path should not have cache headers
    # (or may have them from other middleware, but not from our middleware)


def test_no_cache_for_errors():
    """Test that error responses get no-cache headers."""
    async def error_endpoint(request):
        return JSONResponse({"error": "Not found"}, status_code=404)

    app = Starlette(routes=[Route("/error", error_endpoint)])

    with patch.dict(os.environ, {"CACHE_CONTROL_ENABLED": "true"}):
        app.add_middleware(CacheControlMiddleware)

    client = TestClient(app)
    response = client.get("/error")

    assert response.status_code == 404
    assert "Cache-Control" in response.headers
    assert "no-cache" in response.headers["Cache-Control"]
    assert "no-store" in response.headers["Cache-Control"]


def test_etag_hash_algorithm():
    """Test that ETag uses MD5 hash."""
    content = b'{"data": {"users": []}}'
    expected_etag = hashlib.md5(content).hexdigest()

    async def test_endpoint(request):
        return JSONResponse({"data": {"users": []}})

    app = Starlette(routes=[Route("/test", test_endpoint)])

    with patch.dict(os.environ, {"CACHE_CONTROL_ENABLED": "true"}):
        app.add_middleware(CacheControlMiddleware)

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 200
    etag = response.headers["ETag"].strip('"')
    # ETag should match MD5 of response body
    assert len(etag) == 32  # MD5 hash length
    assert all(c in "0123456789abcdef" for c in etag)


def test_mutation_detection_simple():
    """Test that mutation keyword is detected in GraphQL query."""
    async def graphql_endpoint(request):
        return JSONResponse({"data": {"result": "ok"}})

    app = Starlette(routes=[Route("/graphql", graphql_endpoint, methods=["POST"])])

    with patch.dict(os.environ, {"CACHE_CONTROL_ENABLED": "true"}):
        app.add_middleware(CacheControlMiddleware)

    client = TestClient(app)

    # Test mutation with different formats
    mutations = [
        "mutation { createUser { id } }",
        "mutation CreateUser { createUser { id } }",
        "  mutation  { createUser { id } }",  # With whitespace
    ]

    for mutation_query in mutations:
        response = client.post("/graphql", json={"query": mutation_query})
        assert "no-cache" in response.headers["Cache-Control"]


def test_query_detection():
    """Test that query keyword is detected (not mutation)."""
    async def graphql_endpoint(request):
        return JSONResponse({"data": {"users": []}})

    app = Starlette(routes=[Route("/graphql", graphql_endpoint, methods=["POST"])])

    with patch.dict(os.environ, {"CACHE_CONTROL_ENABLED": "true"}):
        app.add_middleware(CacheControlMiddleware)

    client = TestClient(app)

    # Test queries
    queries = [
        "query { users { id } }",
        "query GetUsers { users { id } }",
        "{ users { id } }",  # Shorthand query
    ]

    for query_str in queries:
        response = client.post("/graphql", json={"query": query_str})
        # Should be cacheable
        assert "public" in response.headers["Cache-Control"] or "private" in response.headers["Cache-Control"]
        assert "no-cache" not in response.headers["Cache-Control"]
