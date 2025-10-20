"""
Middleware for application-wide request/response processing.
"""

from .metrics import PrometheusMiddleware

__all__ = ['PrometheusMiddleware']
