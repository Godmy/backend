from __future__ import annotations

import logging
import os
from typing import Any


_LOGGING_CONFIGURED = False


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def setup_logging() -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log_format = os.getenv(
        "LOG_CONSOLE_FORMAT",
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    logging.basicConfig(level=level, format=log_format)
    root_logger = logging.getLogger()
    request_id_filter = _RequestIdFilter()
    root_logger.addFilter(request_id_filter)
    for handler in root_logger.handlers:
        handler.addFilter(request_id_filter)
    _LOGGING_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)


def bind_logger_extra(logger: logging.Logger, **extra: Any) -> logging.LoggerAdapter:
    return logging.LoggerAdapter(logger, extra)
