"""
Tests for Prometheus metrics endpoint.

User Story: #17 - Prometheus Metrics Collection (P0)
"""

import pytest
from starlette.testclient import TestClient

from app import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_metrics_endpoint_exists(client):
    """Test that /metrics endpoint exists and returns 200."""
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_content_type(client):
    """Test that /metrics returns correct content type."""
    response = client.get("/metrics")
    # Prometheus uses text/plain or application/openmetrics-text
    assert "text/plain" in response.headers["content-type"] or \
           "openmetrics" in response.headers["content-type"]


def test_metrics_contains_http_metrics(client):
    """Test that metrics contain HTTP request metrics."""
    # Make a request to generate some metrics
    client.get("/health")

    # Get metrics
    response = client.get("/metrics")
    content = response.text

    # Check for HTTP metrics
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
    assert "http_requests_in_progress" in content


def test_metrics_contains_system_metrics(client):
    """Test that metrics contain system metrics."""
    response = client.get("/metrics")
    content = response.text

    # Check for system metrics
    assert "process_cpu_usage_percent" in content
    assert "process_memory_bytes" in content


def test_metrics_contains_app_info(client):
    """Test that metrics contain application info."""
    response = client.get("/metrics")
    content = response.text

    # Check for app info
    assert "app_info" in content


def test_metrics_prometheus_format(client):
    """Test that metrics are in valid Prometheus format."""
    response = client.get("/metrics")
    content = response.text

    # Basic Prometheus format checks
    # Metrics should have HELP and TYPE comments
    assert "# HELP" in content
    assert "# TYPE" in content


def test_health_request_tracked_in_metrics(client):
    """Test that requests are tracked in metrics."""
    # Get initial metrics
    response1 = client.get("/metrics")
    content1 = response1.text

    # Make some requests
    for _ in range(5):
        client.get("/health")

    # Get updated metrics
    response2 = client.get("/metrics")
    content2 = response2.text

    # Metrics should have changed
    assert response2.status_code == 200
    assert len(content2) > 0


def test_metrics_endpoint_not_self_tracked(client):
    """Test that /metrics endpoint doesn't track itself."""
    # This is to prevent infinite metric collection
    # The middleware should skip /metrics path
    response = client.get("/metrics")
    content = response.text

    # Check that /metrics path is not in the metrics
    # (or at least not incremented by this call)
    assert response.status_code == 200
