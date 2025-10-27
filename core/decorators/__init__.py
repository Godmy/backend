"""
Decorators for common functionality.

This module provides reusable decorators for service methods including:
- @cached: Redis-based caching for service methods
"""

from core.decorators.cache import cached

__all__ = ["cached"]
