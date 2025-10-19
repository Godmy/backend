"""
Sentry Error Tracking & Monitoring Integration

This module initializes Sentry for automatic error tracking and performance monitoring.
It provides comprehensive error context including user information, request details,
and custom breadcrumbs.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

logger = logging.getLogger(__name__)

# Sensitive data patterns to filter out
SENSITIVE_KEYS = [
    "password",
    "token",
    "secret",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "authorization",
    "cookie",
    "session",
    "csrf",
    "jwt",
]

SENSITIVE_PATTERNS = [
    re.compile(r'"password"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r'"token"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r'"secret"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r"Bearer\s+[\w-]+\.[\w-]+\.[\w-]+", re.IGNORECASE),
]


def filter_sensitive_data(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter sensitive data from Sentry events before sending.

    This function removes passwords, tokens, and other sensitive information
    from the event data to prevent leaking credentials.

    Args:
        event: The Sentry event dict
        hint: Additional context about the event

    Returns:
        The filtered event or None to drop the event
    """
    try:
        # Filter request data
        if "request" in event:
            request = event["request"]

            # Filter headers
            if "headers" in request:
                headers = request["headers"]
                for key in list(headers.keys()):
                    if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
                        headers[key] = "[FILTERED]"

            # Filter cookies
            if "cookies" in request:
                request["cookies"] = "[FILTERED]"

            # Filter query string
            if "query_string" in request and request["query_string"]:
                for key in SENSITIVE_KEYS:
                    if key in request["query_string"].lower():
                        request["query_string"] = "[FILTERED]"

            # Filter POST data
            if "data" in request:
                data = request["data"]
                if isinstance(data, dict):
                    for key in list(data.keys()):
                        if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
                            data[key] = "[FILTERED]"
                elif isinstance(data, str):
                    # Filter string data using patterns
                    for pattern in SENSITIVE_PATTERNS:
                        data = pattern.sub('"[FILTERED]"', data)
                    request["data"] = data

        # Filter extra context
        if "extra" in event:
            extra = event["extra"]
            for key in list(extra.keys()):
                if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
                    extra[key] = "[FILTERED]"

        # Filter user data (keep only safe fields)
        if "user" in event:
            user = event["user"]
            safe_fields = {"id", "username", "email"}
            for key in list(user.keys()):
                if key not in safe_fields:
                    del user[key]

        return event

    except Exception as e:
        logger.error(f"Error filtering sensitive data: {e}")
        # Return event anyway, better to have unfiltered data than lose the error
        return event


def before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Hook called before sending events to Sentry.

    This allows us to modify or drop events before they're sent.
    We use this for filtering sensitive data and adding custom context.

    Args:
        event: The Sentry event dict
        hint: Additional context about the event

    Returns:
        The modified event or None to drop the event
    """
    # Filter sensitive data
    event = filter_sensitive_data(event, hint)

    # Add custom tags
    if "tags" not in event:
        event["tags"] = {}

    # Add environment tag
    event["tags"]["environment"] = os.getenv("ENVIRONMENT", "development")

    # Add service tag
    event["tags"]["service"] = "backend"

    return event


def init_sentry() -> None:
    """
    Initialize Sentry error tracking and monitoring.

    This function sets up Sentry with:
    - Starlette integration for automatic error capture
    - SQLAlchemy integration for database query tracking
    - Logging integration for capturing log messages
    - Performance monitoring with transaction traces
    - Breadcrumbs for user action tracking
    - Sensitive data filtering

    Environment variables:
        SENTRY_DSN: Sentry project DSN (required)
        ENVIRONMENT: Environment name (dev/staging/production)
        SENTRY_TRACES_SAMPLE_RATE: Sample rate for performance monitoring (0.0-1.0)
        SENTRY_ENABLE_TRACING: Enable performance tracing (true/false)
    """
    sentry_dsn = os.getenv("SENTRY_DSN")

    if not sentry_dsn or sentry_dsn == "":
        logger.warning("SENTRY_DSN not configured. Sentry error tracking is disabled.")
        return

    environment = os.getenv("ENVIRONMENT", "development")
    enable_tracing = os.getenv("SENTRY_ENABLE_TRACING", "true").lower() == "true"

    # Sample rate for performance monitoring
    # 1.0 = 100% of transactions, 0.0 = 0% of transactions
    # In production, use lower values like 0.1 (10%) to reduce overhead
    traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0"))
    if environment == "production":
        traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

    # Configure logging integration
    # Capture log messages as breadcrumbs and events
    logging_integration = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Capture errors and above as events
    )

    integrations = [
        StarletteIntegration(
            transaction_style="endpoint",  # Group by endpoint, not by URL
            failed_request_status_codes=[500, 599],  # Only capture 5xx errors
        ),
        SqlalchemyIntegration(),
        logging_integration,
    ]

    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            # Release tracking - link errors to specific deployments
            release=os.getenv("SENTRY_RELEASE", None),
            # Performance monitoring
            traces_sample_rate=traces_sample_rate if enable_tracing else 0.0,
            # Integrations
            integrations=integrations,
            # Callbacks
            before_send=before_send,
            # Additional options
            send_default_pii=False,  # Don't send PII by default
            attach_stacktrace=True,  # Always attach stack traces
            max_breadcrumbs=50,  # Keep last 50 breadcrumbs
            debug=os.getenv("SENTRY_DEBUG", "false").lower() == "true",
        )

        logger.info(
            f"Sentry initialized successfully for environment: {environment}, "
            f"tracing: {enable_tracing}, sample_rate: {traces_sample_rate}"
        )

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def capture_exception(error: Exception, **kwargs) -> Optional[str]:
    """
    Manually capture an exception and send to Sentry.

    Args:
        error: The exception to capture
        **kwargs: Additional context to attach to the event

    Returns:
        Event ID if sent successfully, None otherwise

    Example:
        try:
            risky_operation()
        except Exception as e:
            event_id = capture_exception(e, user_id=user.id, operation="payment")
            logger.error(f"Error captured: {event_id}")
    """
    if not sentry_sdk.Hub.current.client:
        logger.warning("Sentry not initialized, cannot capture exception")
        return None

    with sentry_sdk.push_scope() as scope:
        # Add custom context
        for key, value in kwargs.items():
            scope.set_extra(key, value)

        # Capture and return event ID
        event_id = sentry_sdk.capture_exception(error)
        return event_id


def capture_message(message: str, level: str = "info", **kwargs) -> Optional[str]:
    """
    Manually capture a message and send to Sentry.

    Args:
        message: The message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **kwargs: Additional context to attach to the event

    Returns:
        Event ID if sent successfully, None otherwise

    Example:
        event_id = capture_message(
            "User exceeded rate limit",
            level="warning",
            user_id=user.id,
            endpoint="/graphql"
        )
    """
    if not sentry_sdk.Hub.current.client:
        logger.warning("Sentry not initialized, cannot capture message")
        return None

    with sentry_sdk.push_scope() as scope:
        # Add custom context
        for key, value in kwargs.items():
            scope.set_extra(key, value)

        # Capture and return event ID
        event_id = sentry_sdk.capture_message(message, level=level)
        return event_id


def set_user_context(user_id: int, username: str = None, email: str = None) -> None:
    """
    Set user context for error tracking.

    This associates all subsequent errors with the specified user.

    Args:
        user_id: User ID
        username: Username (optional)
        email: User email (optional)

    Example:
        set_user_context(user_id=123, username="john_doe", email="john@example.com")
    """
    if not sentry_sdk.Hub.current.client:
        return

    sentry_sdk.set_user({"id": user_id, "username": username, "email": email})


def clear_user_context() -> None:
    """Clear user context (e.g., after logout)."""
    if not sentry_sdk.Hub.current.client:
        return

    sentry_sdk.set_user(None)


def add_breadcrumb(message: str, category: str = "default", level: str = "info", **data) -> None:
    """
    Add a breadcrumb to track user actions leading up to an error.

    Breadcrumbs are a trail of events that happened before an error.
    They help understand what the user was doing when the error occurred.

    Args:
        message: Breadcrumb message
        category: Category (e.g., "auth", "query", "navigation")
        level: Severity level (debug, info, warning, error)
        **data: Additional data to attach

    Example:
        add_breadcrumb("User logged in", category="auth", user_id=123)
        add_breadcrumb("Query executed", category="database", query="SELECT * FROM users")
    """
    if not sentry_sdk.Hub.current.client:
        return

    sentry_sdk.add_breadcrumb(message=message, category=category, level=level, data=data)


def set_context(key: str, value: Dict[str, Any]) -> None:
    """
    Set custom context for error tracking.

    Args:
        key: Context key (e.g., "database", "redis", "external_api")
        value: Context data as dict

    Example:
        set_context("database", {
            "query": "SELECT * FROM users WHERE id = ?",
            "duration_ms": 45.2,
            "rows_affected": 1
        })
    """
    if not sentry_sdk.Hub.current.client:
        return

    sentry_sdk.set_context(key, value)


def start_transaction(name: str, op: str = "task") -> Any:
    """
    Start a performance monitoring transaction.

    Transactions track the performance of operations and help identify bottlenecks.

    Args:
        name: Transaction name (e.g., "graphql.query.getUsers")
        op: Operation type (e.g., "task", "http.server", "db.query")

    Returns:
        Transaction object or None if tracing disabled

    Example:
        with start_transaction("process_payment", op="task") as transaction:
            # Do work
            transaction.set_tag("user_id", user.id)
            transaction.set_data("amount", 100.50)
    """
    if not sentry_sdk.Hub.current.client:
        return None

    return sentry_sdk.start_transaction(name=name, op=op)
