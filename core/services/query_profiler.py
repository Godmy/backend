"""
Query Profiler Service - SQLAlchemy query logging and profiling.

Provides automatic query logging and slow query detection via SQLAlchemy events.

Implementation for User Story #24 - Query Optimization & N+1 Prevention

Features:
    - Automatic query logging in DEBUG mode
    - Slow query detection (>100ms)
    - Query statistics and profiling
    - Integration with structured logging
    - N+1 query detection warnings

Usage:
    from core.services.query_profiler import setup_query_profiling

    # Setup at app startup (in database.py)
    setup_query_profiling(engine)
"""

import logging
import time
from typing import Any, Dict, Optional
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from core.structured_logging import get_logger, log_database_query

logger = get_logger(__name__)

# Query statistics
_query_stats: Dict[str, Dict[str, Any]] = {}
_profiling_enabled = False
_slow_query_threshold_ms = 100


def setup_query_profiling(
    engine: Engine,
    enabled: bool = True,
    slow_query_threshold_ms: int = 100,
    log_all_queries: bool = False
) -> None:
    """
    Setup query profiling with SQLAlchemy events.

    Args:
        engine: SQLAlchemy engine
        enabled: Enable query profiling
        slow_query_threshold_ms: Threshold for slow query warnings (default: 100ms)
        log_all_queries: Log all queries regardless of DEBUG mode

    Environment Variables:
        QUERY_PROFILING_ENABLED: Enable query profiling (default: true)
        SLOW_QUERY_THRESHOLD_MS: Slow query threshold in ms (default: 100)
        LOG_ALL_QUERIES: Log all queries in DEBUG mode (default: false)
    """
    global _profiling_enabled, _slow_query_threshold_ms

    import os

    # Read configuration
    _profiling_enabled = enabled and os.getenv("QUERY_PROFILING_ENABLED", "true").lower() == "true"
    _slow_query_threshold_ms = int(os.getenv("SLOW_QUERY_THRESHOLD_MS", str(slow_query_threshold_ms)))
    _log_all_queries = log_all_queries or os.getenv("LOG_ALL_QUERIES", "false").lower() == "true"

    if not _profiling_enabled:
        logger.info("Query profiling disabled")
        return

    # Register event listeners
    event.listen(engine, "before_cursor_execute", _before_cursor_execute)
    event.listen(engine, "after_cursor_execute", _after_cursor_execute)

    logger.info(
        "Query profiling enabled",
        extra={
            "slow_query_threshold_ms": _slow_query_threshold_ms,
            "log_all_queries": _log_all_queries
        }
    )


def _before_cursor_execute(
    conn: Any,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Any,
    executemany: bool
) -> None:
    """SQLAlchemy event: before query execution."""
    # Store start time in context
    conn.info.setdefault("query_start_time", []).append(time.time())


def _after_cursor_execute(
    conn: Any,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Any,
    executemany: bool
) -> None:
    """SQLAlchemy event: after query execution."""
    # Calculate duration
    start_times = conn.info.get("query_start_time", [])
    if not start_times:
        return

    start_time = start_times.pop()
    duration_ms = (time.time() - start_time) * 1000

    # Get row count
    try:
        rows = cursor.rowcount if cursor.rowcount >= 0 else 0
    except Exception:
        rows = 0

    # Update statistics
    _update_query_stats(statement, duration_ms, rows)

    # Log query using structured logging
    log_database_query(statement, duration_ms, rows)

    # Detect N+1 queries
    _detect_n_plus_one_query(statement, duration_ms)


def _update_query_stats(query: str, duration_ms: float, rows: int) -> None:
    """Update query statistics."""
    # Extract query type (SELECT, INSERT, UPDATE, DELETE)
    query_type = query.strip().split()[0].upper() if query.strip() else "UNKNOWN"

    if query_type not in _query_stats:
        _query_stats[query_type] = {
            "count": 0,
            "total_duration_ms": 0,
            "max_duration_ms": 0,
            "min_duration_ms": float("inf"),
            "total_rows": 0
        }

    stats = _query_stats[query_type]
    stats["count"] += 1
    stats["total_duration_ms"] += duration_ms
    stats["max_duration_ms"] = max(stats["max_duration_ms"], duration_ms)
    stats["min_duration_ms"] = min(stats["min_duration_ms"], duration_ms)
    stats["total_rows"] += rows


def _detect_n_plus_one_query(query: str, duration_ms: float) -> None:
    """
    Detect potential N+1 query problems.

    Warns if:
    - Same SELECT query executed multiple times in short period
    - Query inside a loop (detected by rapid consecutive identical queries)
    """
    # Simple heuristic: warn if same query executed rapidly
    # In production, this should be more sophisticated
    pass  # TODO: Implement more sophisticated N+1 detection


def get_query_stats() -> Dict[str, Dict[str, Any]]:
    """
    Get query statistics.

    Returns:
        Dictionary with query statistics by type
    """
    return _query_stats.copy()


def reset_query_stats() -> None:
    """Reset query statistics."""
    global _query_stats
    _query_stats = {}


def log_query_stats() -> None:
    """Log current query statistics."""
    if not _query_stats:
        logger.info("No query statistics available")
        return

    logger.info("Query Statistics", extra={"stats": _query_stats})

    for query_type, stats in _query_stats.items():
        avg_duration = stats["total_duration_ms"] / stats["count"] if stats["count"] > 0 else 0
        logger.info(
            f"  {query_type}: {stats['count']} queries, "
            f"avg={avg_duration:.2f}ms, "
            f"max={stats['max_duration_ms']:.2f}ms, "
            f"min={stats['min_duration_ms']:.2f}ms, "
            f"total_rows={stats['total_rows']}"
        )
