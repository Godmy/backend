"""
Structured Logging System with JSON Format.

Provides JSON-formatted logging for easy parsing in ELK/CloudWatch/Grafana Loki.

Implementation for User Story #19 - Structured Logging (JSON Format) (P0)

Features:
    - JSON format logging for all logs
    - Fields: timestamp, level, message, request_id, user_id, endpoint, logger, module
    - Correlation ID for request tracing
    - Log rotation by size and time
    - Separate log files: access.log, error.log, app.log
    - ELK/CloudWatch compatible
    - Environment-based configuration

Usage:
    from core.structured_logging import setup_logging, get_logger

    # Setup logging (once at app startup)
    setup_logging()

    # Get logger
    logger = get_logger(__name__)
    logger.info("User logged in", extra={"user_id": 123, "ip": "1.2.3.4"})
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from pythonjsonlogger import jsonlogger
except ImportError:
    jsonlogger = None  # Fallback to regular logging if not installed

from core.context import get_request_id, get_user_id


class CustomJsonFormatter(jsonlogger.JsonFormatter if jsonlogger else logging.Formatter):
    """
    Custom JSON formatter that includes request context.

    Adds fields:
        - timestamp (ISO 8601)
        - level (INFO, ERROR, etc.)
        - message
        - request_id
        - user_id
        - logger (logger name)
        - module (file name)
        - function (function name)
        - line (line number)
        - extra fields from log record
    """

    def add_fields(self, log_record, record, message_dict):
        """Add custom fields to JSON log record."""
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        # Add timestamp in ISO 8601 format
        log_record['timestamp'] = datetime.now(timezone.utc).isoformat()

        # Add log level
        log_record['level'] = record.levelname

        # Add logger name
        log_record['logger'] = record.name

        # Add source location
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno

        # Add request context
        request_id = get_request_id()
        user_id = get_user_id()

        if request_id and request_id != "-":
            log_record['request_id'] = request_id

        if user_id and user_id != "-":
            log_record['user_id'] = user_id

        # Add endpoint from record if available
        if hasattr(record, 'endpoint'):
            log_record['endpoint'] = record.endpoint

        # Move message to top level
        if 'message' not in log_record and message_dict.get('message'):
            log_record['message'] = message_dict['message']


class FallbackFormatter(logging.Formatter):
    """Fallback formatter when python-json-logger is not available."""

    def format(self, record):
        """Format log record with context."""
        # Add request context
        request_id = get_request_id()
        user_id = get_user_id()

        record.request_id = request_id if request_id and request_id != "-" else "-"
        record.user_id = user_id if user_id and user_id != "-" else "-"

        return super().format(record)


def setup_logging(
    log_level: Optional[str] = None,
    log_dir: Optional[str] = None,
    use_json: Optional[bool] = None,
    rotation_size: int = 10 * 1024 * 1024,  # 10MB
    rotation_backup_count: int = 5
) -> None:
    """
    Setup structured logging with JSON format.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: logs/)
        use_json: Use JSON format (default: True if python-json-logger installed)
        rotation_size: Max log file size in bytes before rotation
        rotation_backup_count: Number of backup files to keep

    Environment Variables:
        LOG_LEVEL: Log level (default: INFO)
        LOG_DIR: Log directory (default: logs)
        LOG_FORMAT: "json" or "text" (default: json)
        LOG_ROTATION_SIZE_MB: Max file size in MB before rotation (default: 10)
        LOG_ROTATION_BACKUP_COUNT: Number of backup files (default: 5)
        LOG_FILE_ENABLED: Enable file logging (default: true)
        LOG_CONSOLE_FORMAT: Text format for console logs (default: "%(asctime)s %(levelname)s [%(request_id)s] %(message)s")
        LOG_CONSOLE_JSON: Use JSON formatting for console logs (default: false)
        LOG_SUPPRESS_UVICORN_ACCESS: Disable Uvicorn access logs (default: true)
    """
    # Get configuration from environment
    log_level = log_level or os.getenv("LOG_LEVEL", "INFO").upper()
    log_dir = log_dir or os.getenv("LOG_DIR", "logs")
    log_format = os.getenv("LOG_FORMAT", "json").lower()

    # Check if JSON format is available and requested
    if use_json is None:
        use_json = jsonlogger is not None and log_format == "json"

    # Override if python-json-logger is not installed
    if use_json and jsonlogger is None:
        print("Warning: python-json-logger not installed, falling back to text format")
        use_json = False

    # Parse rotation settings from environment
    try:
        rotation_size = int(os.getenv("LOG_ROTATION_SIZE_MB", "10")) * 1024 * 1024
    except ValueError:
        rotation_size = 10 * 1024 * 1024

    try:
        rotation_backup_count = int(os.getenv("LOG_ROTATION_BACKUP_COUNT", "5"))
    except ValueError:
        rotation_backup_count = 5

    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create formatters
    if use_json:
        # JSON formatter for file handlers
        json_format = "%(timestamp)s %(level)s %(name)s %(message)s"
        file_formatter = CustomJsonFormatter(json_format)
    else:
        # Text formatter with context for file handlers
        text_format = "[%(request_id)s] [user:%(user_id)s] %(levelname)s - %(name)s - %(message)s"
        file_formatter = FallbackFormatter(text_format)

    console_use_json = os.getenv("LOG_CONSOLE_JSON", "false").lower() == "true"
    if console_use_json and not use_json:
        # Respect request but JSON formatter unavailable, fallback to text
        console_use_json = False

    if console_use_json:
        console_formatter = file_formatter
    else:
        console_format = os.getenv(
            "LOG_CONSOLE_FORMAT",
            "%(asctime)s %(levelname)s [%(request_id)s] %(message)s"
        )
        console_formatter = FallbackFormatter(console_format)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler (always enabled for Docker/Kubernetes)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handlers (enabled by default for observability)
    enable_file_logging = os.getenv("LOG_FILE_ENABLED", "true").lower() == "true"

    if enable_file_logging:
        # App log (all logs)
        app_handler = logging.handlers.RotatingFileHandler(
            log_path / "app.log",
            maxBytes=rotation_size,
            backupCount=rotation_backup_count
        )
        app_handler.setLevel(logging.DEBUG)
        app_handler.setFormatter(file_formatter)
        root_logger.addHandler(app_handler)

        # Access log (INFO and below)
        access_handler = logging.handlers.RotatingFileHandler(
            log_path / "access.log",
            maxBytes=rotation_size,
            backupCount=rotation_backup_count
        )
        access_handler.setLevel(logging.INFO)
        access_handler.addFilter(lambda record: record.levelno <= logging.INFO)
        access_handler.setFormatter(file_formatter)
        root_logger.addHandler(access_handler)

        # Error log (WARNING and above)
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / "error.log",
            maxBytes=rotation_size,
            backupCount=rotation_backup_count
        )
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)

    # Harmonize uvicorn loggers to avoid duplicated noisy output
    suppress_uvicorn_access = os.getenv("LOG_SUPPRESS_UVICORN_ACCESS", "true").lower() == "true"
    uvicorn_log_level = getattr(logging, log_level)

    for logger_name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.setLevel(uvicorn_log_level)
        uvicorn_logger.propagate = True

    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers.clear()
    if suppress_uvicorn_access:
        uvicorn_access_logger.propagate = False
        uvicorn_access_logger.disabled = True
    else:
        uvicorn_access_logger.disabled = False
        uvicorn_access_logger.setLevel(uvicorn_log_level)
        uvicorn_access_logger.propagate = True

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Structured logging initialized",
        extra={
            "log_level": log_level,
            "log_format": "json" if use_json else "text",
            "file_logging": enable_file_logging
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance with structured logging support.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("User action", extra={"user_id": 123, "action": "login"})
    """
    return logging.getLogger(name)


# Convenience functions for common log patterns

def log_api_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: int,
    user_id: Optional[int] = None
) -> None:
    """
    Log API request in structured format.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        user_id: User ID (optional)
    """
    logger = get_logger("api")

    log_data = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "endpoint": f"{method} {path}"
    }

    if user_id:
        log_data["user_id"] = user_id

    # Choose log level based on status code
    if status_code >= 500:
        logger.error(f"{method} {path} {status_code} ({duration_ms}ms)", extra=log_data)
    elif status_code >= 400:
        logger.warning(f"{method} {path} {status_code} ({duration_ms}ms)", extra=log_data)
    else:
        logger.info(f"{method} {path} {status_code} ({duration_ms}ms)", extra=log_data)


def log_database_query(query: str, duration_ms: float, rows: int = 0) -> None:
    """
    Log database query in structured format.

    Args:
        query: SQL query (truncated)
        duration_ms: Query duration in milliseconds
        rows: Number of rows affected/returned
    """
    logger = get_logger("database")

    # Truncate long queries
    query_preview = query[:200] + "..." if len(query) > 200 else query

    log_data = {
        "query": query_preview,
        "duration_ms": duration_ms,
        "rows": rows
    }

    # Warn on slow queries
    if duration_ms > 100:
        logger.warning(f"Slow query ({duration_ms}ms): {query_preview}", extra=log_data)
    else:
        logger.debug(f"Query ({duration_ms}ms): {query_preview}", extra=log_data)


def log_business_event(
    event: str,
    user_id: Optional[int] = None,
    **kwargs
) -> None:
    """
    Log business event in structured format.

    Args:
        event: Event name (e.g., "user_registered", "file_uploaded")
        user_id: User ID (optional)
        **kwargs: Additional event data
    """
    logger = get_logger("business")

    log_data = {"event": event, **kwargs}

    if user_id:
        log_data["user_id"] = user_id

    logger.info(f"Business event: {event}", extra=log_data)
