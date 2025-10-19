"""
Tests for Sentry error tracking integration
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from core.sentry import (
    add_breadcrumb,
    capture_exception,
    capture_message,
    filter_sensitive_data,
    init_sentry,
    set_user_context,
)


class TestSentryIntegration:
    """Test Sentry integration functionality"""

    def test_init_sentry_without_dsn(self, caplog):
        """Test that Sentry initialization is skipped when DSN is not configured"""
        with patch.dict(os.environ, {"SENTRY_DSN": ""}, clear=True):
            init_sentry()
            assert "SENTRY_DSN not configured" in caplog.text

    @patch("core.sentry.sentry_sdk.init")
    def test_init_sentry_with_dsn(self, mock_init):
        """Test that Sentry is initialized when DSN is provided"""
        test_dsn = "https://test@sentry.io/123"
        with patch.dict(
            os.environ,
            {
                "SENTRY_DSN": test_dsn,
                "ENVIRONMENT": "test",
                "SENTRY_ENABLE_TRACING": "true",
                "SENTRY_TRACES_SAMPLE_RATE": "1.0",
            },
        ):
            init_sentry()
            mock_init.assert_called_once()
            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["dsn"] == test_dsn
            assert call_kwargs["environment"] == "test"
            assert call_kwargs["traces_sample_rate"] == 1.0

    def test_filter_sensitive_headers(self):
        """Test that sensitive headers are filtered"""
        event = {
            "request": {
                "headers": {
                    "Authorization": "Bearer secret_token",
                    "Cookie": "session=abc123",
                    "Content-Type": "application/json",
                }
            }
        }

        filtered = filter_sensitive_data(event, {})

        assert filtered["request"]["headers"]["Authorization"] == "[FILTERED]"
        assert filtered["request"]["headers"]["Cookie"] == "[FILTERED]"
        assert filtered["request"]["headers"]["Content-Type"] == "application/json"

    def test_filter_sensitive_post_data(self):
        """Test that sensitive POST data is filtered"""
        event = {
            "request": {
                "data": {
                    "username": "john_doe",
                    "password": "secret123",
                    "email": "john@example.com",
                    "token": "abc123",
                }
            }
        }

        filtered = filter_sensitive_data(event, {})

        assert filtered["request"]["data"]["username"] == "john_doe"
        assert filtered["request"]["data"]["password"] == "[FILTERED]"
        assert filtered["request"]["data"]["email"] == "john@example.com"
        assert filtered["request"]["data"]["token"] == "[FILTERED]"

    def test_filter_sensitive_string_data(self):
        """Test that sensitive data in string format is filtered"""
        event = {
            "request": {
                "data": '{"username": "john", "password": "secret123", "token": "abc"}'
            }
        }

        filtered = filter_sensitive_data(event, {})

        # Check that password and token were filtered
        assert "secret123" not in filtered["request"]["data"]
        assert "[FILTERED]" in filtered["request"]["data"]

    def test_filter_user_data(self):
        """Test that only safe user fields are kept"""
        event = {
            "user": {
                "id": 123,
                "username": "john_doe",
                "email": "john@example.com",
                "password_hash": "hashed_password",
                "session_token": "abc123",
            }
        }

        filtered = filter_sensitive_data(event, {})

        # Safe fields should be kept
        assert filtered["user"]["id"] == 123
        assert filtered["user"]["username"] == "john_doe"
        assert filtered["user"]["email"] == "john@example.com"

        # Unsafe fields should be removed
        assert "password_hash" not in filtered["user"]
        assert "session_token" not in filtered["user"]

    @patch("core.sentry.sentry_sdk.Hub")
    def test_capture_exception_without_sentry(self, mock_hub):
        """Test capture_exception when Sentry is not initialized"""
        mock_hub.current.client = None

        result = capture_exception(Exception("test error"))

        assert result is None

    @patch("core.sentry.sentry_sdk.Hub")
    @patch("core.sentry.sentry_sdk.capture_exception")
    @patch("core.sentry.sentry_sdk.push_scope")
    def test_capture_exception_with_context(self, mock_push_scope, mock_capture, mock_hub):
        """Test capture_exception with custom context"""
        mock_hub.current.client = MagicMock()
        mock_scope = MagicMock()
        mock_push_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
        mock_push_scope.return_value.__exit__ = MagicMock(return_value=False)
        mock_capture.return_value = "event_id_123"

        error = Exception("test error")
        event_id = capture_exception(error, user_id=123, operation="test")

        assert event_id == "event_id_123"
        mock_capture.assert_called_once_with(error)
        mock_scope.set_extra.assert_any_call("user_id", 123)
        mock_scope.set_extra.assert_any_call("operation", "test")

    @patch("core.sentry.sentry_sdk.Hub")
    @patch("core.sentry.sentry_sdk.capture_message")
    @patch("core.sentry.sentry_sdk.push_scope")
    def test_capture_message_with_level(self, mock_push_scope, mock_capture, mock_hub):
        """Test capture_message with severity level"""
        mock_hub.current.client = MagicMock()
        mock_scope = MagicMock()
        mock_push_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
        mock_push_scope.return_value.__exit__ = MagicMock(return_value=False)
        mock_capture.return_value = "event_id_456"

        event_id = capture_message("Test warning", level="warning", user_id=123)

        assert event_id == "event_id_456"
        mock_capture.assert_called_once_with("Test warning", level="warning")
        mock_scope.set_extra.assert_called_once_with("user_id", 123)

    @patch("core.sentry.sentry_sdk.Hub")
    @patch("core.sentry.sentry_sdk.set_user")
    def test_set_user_context(self, mock_set_user, mock_hub):
        """Test setting user context"""
        mock_hub.current.client = MagicMock()

        set_user_context(user_id=123, username="john_doe", email="john@example.com")

        mock_set_user.assert_called_once_with(
            {"id": 123, "username": "john_doe", "email": "john@example.com"}
        )

    @patch("core.sentry.sentry_sdk.Hub")
    @patch("core.sentry.sentry_sdk.add_breadcrumb")
    def test_add_breadcrumb(self, mock_add_breadcrumb, mock_hub):
        """Test adding breadcrumbs"""
        mock_hub.current.client = MagicMock()

        add_breadcrumb("User logged in", category="auth", level="info", user_id=123)

        mock_add_breadcrumb.assert_called_once_with(
            message="User logged in",
            category="auth",
            level="info",
            data={"user_id": 123},
        )

    def test_filter_sensitive_data_handles_exceptions(self):
        """Test that filter handles exceptions gracefully"""
        # Malformed event that might cause errors
        event = {"request": {"headers": None}}

        # Should not raise exception
        filtered = filter_sensitive_data(event, {})

        assert filtered is not None
        assert "request" in filtered


class TestSentryConfiguration:
    """Test Sentry configuration options"""

    @patch("core.sentry.sentry_sdk.init")
    def test_production_sample_rate(self, mock_init):
        """Test that production uses lower sample rate by default"""
        with patch.dict(
            os.environ,
            {
                "SENTRY_DSN": "https://test@sentry.io/123",
                "ENVIRONMENT": "production",
                "SENTRY_ENABLE_TRACING": "true",
            },
        ):
            init_sentry()
            call_kwargs = mock_init.call_args[1]
            # Production should default to 0.1
            assert call_kwargs["traces_sample_rate"] == 0.1

    @patch("core.sentry.sentry_sdk.init")
    def test_development_sample_rate(self, mock_init):
        """Test that development uses higher sample rate by default"""
        with patch.dict(
            os.environ,
            {
                "SENTRY_DSN": "https://test@sentry.io/123",
                "ENVIRONMENT": "development",
                "SENTRY_ENABLE_TRACING": "true",
            },
        ):
            init_sentry()
            call_kwargs = mock_init.call_args[1]
            # Development should default to 1.0
            assert call_kwargs["traces_sample_rate"] == 1.0

    @patch("core.sentry.sentry_sdk.init")
    def test_tracing_disabled(self, mock_init):
        """Test that tracing can be disabled"""
        with patch.dict(
            os.environ,
            {
                "SENTRY_DSN": "https://test@sentry.io/123",
                "ENVIRONMENT": "test",
                "SENTRY_ENABLE_TRACING": "false",
            },
        ):
            init_sentry()
            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["traces_sample_rate"] == 0.0
