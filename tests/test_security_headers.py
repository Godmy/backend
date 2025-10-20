"""
Tests for Security Headers Middleware.

Tests that security headers are properly added to all HTTP responses.
"""

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from core.middleware.security_headers import SecurityHeadersMiddleware


@pytest.fixture
def app():
    """Create a test Starlette app with SecurityHeadersMiddleware."""

    async def homepage(request):
        return PlainTextResponse("Hello, world!")

    test_app = Starlette(routes=[Route("/", homepage)])
    test_app.add_middleware(SecurityHeadersMiddleware)
    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


def test_security_headers_present(client):
    """Test that all security headers are present in response."""
    response = client.get("/")

    assert response.status_code == 200
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "X-XSS-Protection" in response.headers
    assert "Content-Security-Policy" in response.headers
    assert "Referrer-Policy" in response.headers
    assert "Permissions-Policy" in response.headers


def test_x_content_type_options(client):
    """Test X-Content-Type-Options header value."""
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_x_frame_options(client):
    """Test X-Frame-Options header value."""
    response = client.get("/")
    assert response.headers["X-Frame-Options"] == "DENY"


def test_x_xss_protection(client):
    """Test X-XSS-Protection header value."""
    response = client.get("/")
    assert response.headers["X-XSS-Protection"] == "1; mode=block"


def test_content_security_policy(client):
    """Test Content-Security-Policy header is present and has restrictions."""
    response = client.get("/")
    csp = response.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp or "default-src" in csp


def test_referrer_policy(client):
    """Test Referrer-Policy header value."""
    response = client.get("/")
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_permissions_policy(client):
    """Test Permissions-Policy header restricts features."""
    response = client.get("/")
    permissions = response.headers["Permissions-Policy"]

    # Check that dangerous features are restricted
    assert "geolocation=()" in permissions
    assert "microphone=()" in permissions
    assert "camera=()" in permissions
    assert "payment=()" in permissions


def test_hsts_not_in_dev(client, monkeypatch):
    """Test that HSTS is not added in development environment."""
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("HSTS_ENABLED", raising=False)

    response = client.get("/")
    assert "Strict-Transport-Security" not in response.headers


def test_hsts_in_production(client, monkeypatch):
    """Test that HSTS is added in production environment."""
    monkeypatch.setenv("ENVIRONMENT", "production")

    # Create new app with production env
    async def homepage(request):
        return PlainTextResponse("Hello, world!")

    test_app = Starlette(routes=[Route("/", homepage)])
    test_app.add_middleware(SecurityHeadersMiddleware)
    prod_client = TestClient(test_app)

    response = prod_client.get("/")
    assert "Strict-Transport-Security" in response.headers
    hsts = response.headers["Strict-Transport-Security"]
    assert "max-age=" in hsts
    assert "includeSubDomains" in hsts


def test_middleware_can_be_disabled(monkeypatch):
    """Test that middleware can be disabled via environment variable."""
    monkeypatch.setenv("SECURITY_HEADERS_ENABLED", "false")

    async def homepage(request):
        return PlainTextResponse("Hello, world!")

    test_app = Starlette(routes=[Route("/", homepage)])
    test_app.add_middleware(SecurityHeadersMiddleware)
    disabled_client = TestClient(test_app)

    response = disabled_client.get("/")

    # Headers should not be present when disabled
    assert "X-Content-Type-Options" not in response.headers
    assert "X-Frame-Options" not in response.headers


def test_custom_csp_policy(monkeypatch):
    """Test that CSP policy can be customized via environment."""
    custom_csp = "default-src 'self'; script-src 'self' https://cdn.example.com"
    monkeypatch.setenv("CSP_POLICY", custom_csp)

    async def homepage(request):
        return PlainTextResponse("Hello, world!")

    test_app = Starlette(routes=[Route("/", homepage)])
    test_app.add_middleware(SecurityHeadersMiddleware)
    custom_client = TestClient(test_app)

    response = custom_client.get("/")
    assert response.headers["Content-Security-Policy"] == custom_csp


def test_custom_frame_options(monkeypatch):
    """Test that X-Frame-Options can be customized."""
    monkeypatch.setenv("FRAME_OPTIONS", "SAMEORIGIN")

    async def homepage(request):
        return PlainTextResponse("Hello, world!")

    test_app = Starlette(routes=[Route("/", homepage)])
    test_app.add_middleware(SecurityHeadersMiddleware)
    custom_client = TestClient(test_app)

    response = custom_client.get("/")
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"


def test_headers_on_error_responses(client):
    """Test that security headers are added even on error responses."""
    # Request non-existent endpoint
    response = client.get("/nonexistent")

    # Should still have security headers even on 404
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "X-XSS-Protection" in response.headers
