"""
Prometheus metrics collection.

Provides comprehensive metrics for monitoring application performance,
resource usage, and business logic.

User Story: #17 - Prometheus Metrics Collection (P0)
"""

import os
import psutil
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, REGISTRY
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST


# ============================================================================
# APPLICATION INFO
# ============================================================================

app_info = Info('app', 'Application information')
app_info.info({
    'version': '0.3.0',
    'environment': os.getenv('ENVIRONMENT', 'development'),
    'python_version': '3.11'
})


# ============================================================================
# HTTP REQUEST METRICS
# ============================================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)


# ============================================================================
# GRAPHQL METRICS
# ============================================================================

graphql_query_duration_seconds = Histogram(
    'graphql_query_duration_seconds',
    'GraphQL query duration in seconds',
    ['operation_type', 'operation_name'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

graphql_query_errors_total = Counter(
    'graphql_query_errors_total',
    'Total GraphQL query errors',
    ['operation_type', 'operation_name', 'error_type']
)


# ============================================================================
# DATABASE METRICS
# ============================================================================

db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

db_errors_total = Counter(
    'db_errors_total',
    'Total database errors',
    ['error_type']
)


# ============================================================================
# REDIS METRICS
# ============================================================================

redis_connections_active = Gauge(
    'redis_connections_active',
    'Number of active Redis connections'
)

redis_commands_total = Counter(
    'redis_commands_total',
    'Total Redis commands executed',
    ['command']
)


# ============================================================================
# BUSINESS LOGIC METRICS
# ============================================================================

users_registered_total = Counter(
    'users_registered_total',
    'Total number of users registered',
    ['method']  # 'email', 'google', 'telegram'
)

emails_sent_total = Counter(
    'emails_sent_total',
    'Total number of emails sent',
    ['email_type', 'status']  # email_type: 'verification', 'reset', etc. status: 'success', 'error'
)

files_uploaded_total = Counter(
    'files_uploaded_total',
    'Total number of files uploaded',
    ['file_type']  # 'avatar', 'attachment', etc.
)


# ============================================================================
# SYSTEM METRICS
# ============================================================================

process_cpu_usage_percent = Gauge(
    'process_cpu_usage_percent',
    'Process CPU usage in percent'
)

process_memory_bytes = Gauge(
    'process_memory_bytes',
    'Process memory usage in bytes'
)

process_open_fds = Gauge(
    'process_open_fds',
    'Number of open file descriptors'
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def update_system_metrics():
    """Update system metrics (CPU, memory, file descriptors)."""
    try:
        process = psutil.Process()

        # CPU usage
        cpu_percent = process.cpu_percent(interval=None)
        process_cpu_usage_percent.set(cpu_percent)

        # Memory usage
        memory_info = process.memory_info()
        process_memory_bytes.set(memory_info.rss)

        # Open file descriptors (Unix-like systems only)
        if hasattr(process, 'num_fds'):
            process_open_fds.set(process.num_fds())
    except Exception:
        # Silently fail if system metrics are not available
        pass


def get_metrics() -> tuple[bytes, str]:
    """
    Generate metrics in Prometheus format.

    Returns:
        Tuple of (metrics_bytes, content_type)
    """
    # Update system metrics before generating output
    update_system_metrics()

    # Generate metrics
    metrics = generate_latest(REGISTRY)
    return metrics, CONTENT_TYPE_LATEST
