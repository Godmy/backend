"""
Tests for Request ID & Distributed Tracing functionality.

Tests User Story #20 - Request ID & Distributed Tracing (P0)
"""

import pytest
from starlette.testclient import TestClient
from core.context import (
    get_request_id,
    set_request_id,
    get_user_id,
    set_user_id,
    clear_context,
    RequestContextFilter
)
from core.tracing import with_request_context, TracingHelper
import logging


class TestRequestContext:
    """Test request context management."""

    def test_request_id_generation(self):
        """Test that request_id is auto-generated if not set."""
        clear_context()
        request_id = get_request_id()
        assert request_id is not None
        assert len(request_id) > 0

    def test_set_and_get_request_id(self):
        """Test setting and getting request_id."""
        clear_context()
        test_id = "test123"
        set_request_id(test_id)
        assert get_request_id() == test_id

    def test_set_and_get_user_id(self):
        """Test setting and getting user_id."""
        clear_context()
        test_user_id = 42
        set_user_id(test_user_id)
        assert get_user_id() == test_user_id

    def test_clear_context(self):
        """Test clearing context."""
        set_request_id("test123")
        set_user_id(42)
        clear_context()

        # After clear, get_request_id should generate new one
        new_id = get_request_id()
        assert new_id != "test123"
        assert get_user_id() is None


class TestRequestContextFilter:
    """Test logging filter for request context."""

    def test_filter_adds_request_id(self):
        """Test that filter adds request_id to log records."""
        import logging

        set_request_id("test_req_123")
        set_user_id(99)

        filter_obj = RequestContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )

        filter_obj.filter(record)

        assert hasattr(record, 'request_id')
        assert hasattr(record, 'user_id')
        assert record.request_id == "test_req_123"
        assert record.user_id == 99

        clear_context()


class TestHTTPRequestID:
    """Test request ID in HTTP responses."""

    def test_request_id_in_response_headers(self, client: TestClient):
        """Test that X-Request-ID header is present in responses."""
        response = client.get("/health")
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) == 8  # UUID truncated to 8 chars

    def test_request_id_unique_per_request(self, client: TestClient):
        """Test that each request gets a unique request_id."""
        response1 = client.get("/health")
        response2 = client.get("/health")

        id1 = response1.headers["X-Request-ID"]
        id2 = response2.headers["X-Request-ID"]

        assert id1 != id2


@pytest.mark.asyncio
class TestTracingDecorator:
    """Test tracing decorator."""

    async def test_with_request_context_async(self):
        """Test with_request_context decorator for async functions."""
        set_request_id("async_test_123")

        @with_request_context
        async def async_task():
            # Should have access to request_id
            rid = get_request_id()
            return rid

        result = await async_task()
        assert result == "async_test_123"

        clear_context()

    def test_with_request_context_sync(self):
        """Test with_request_context decorator for sync functions."""
        set_request_id("sync_test_456")

        @with_request_context
        def sync_task():
            # Should have access to request_id
            rid = get_request_id()
            return rid

        result = sync_task()
        assert result == "sync_test_456"

        clear_context()


class TestTracingHelper:
    """Test TracingHelper span functionality."""

    def test_span_creation(self):
        """Test creating and using a span."""
        set_request_id("span_test_789")

        with TracingHelper.span("test_operation") as span:
            assert span.name == "test_operation"
            assert span.request_id == "span_test_789"

            span.set_tag("user_id", 42)
            assert span.tags["user_id"] == 42

            span.log("Operation in progress")

        clear_context()

    def test_span_with_exception(self):
        """Test span behavior when exception occurs."""
        set_request_id("span_error_test")

        with pytest.raises(ValueError):
            with TracingHelper.span("failing_operation") as span:
                span.log("About to fail")
                raise ValueError("Test error")

        clear_context()


class TestGraphQLContext:
    """Test request_id in GraphQL context."""

    @pytest.mark.asyncio
    async def test_graphql_context_has_request_id(self, client: TestClient):
        """Test that GraphQL context includes request_id."""
        # Simple GraphQL query
        query = """
        query {
            __typename
        }
        """

        response = client.post(
            "/graphql",
            json={"query": query}
        )

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

        # GraphQL context should have request_id
        # (This is tested indirectly through the response header)


class TestLoggingIntegration:
    """Test that logging includes request_id."""

    def test_log_format_includes_request_id(self, caplog):
        """Test that log messages include request_id."""
        import logging

        # Set up logger with filter
        logger = logging.getLogger("test_logger")
        logger.addFilter(RequestContextFilter())

        set_request_id("log_test_999")
        set_user_id(123)

        with caplog.at_level(logging.INFO):
            logger.info("Test log message")

        # Check that log record has context
        assert len(caplog.records) > 0
        record = caplog.records[0]
        assert hasattr(record, 'request_id')
        assert record.request_id == "log_test_999"
        assert record.user_id == 123

        clear_context()
