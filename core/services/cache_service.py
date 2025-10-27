"""
Cache management service for Redis-based caching.

Provides utilities for:
- Cache invalidation (by pattern or specific key)
- Cache statistics
- Cache health checks
- Bulk cache operations

Implementation for User Story #3 - Redis Service-Level Caching (P2)

Usage:
    from core.services.cache_service import (
        invalidate_cache,
        clear_all_cache,
        get_cache_stats,
        get_cache_health
    )

    # Invalidate specific cache pattern
    await invalidate_cache("cache:language:*")

    # Clear all cache
    await clear_all_cache()

    # Get cache statistics
    stats = await get_cache_stats()

    # Check cache health
    health = await get_cache_health()
"""

import os
from typing import Dict, List, Optional

from core.redis_client import redis_client
from core.structured_logging import get_logger

logger = get_logger(__name__)

# Configuration
MAX_CACHE_KEYS = int(os.getenv("SERVICE_CACHE_MAX_KEYS", "10000"))


async def invalidate_cache(pattern: str) -> int:
    """
    Invalidate (delete) cache entries matching pattern.

    Args:
        pattern: Redis key pattern (e.g., "cache:language:*", "cache:concept:get_all:*")

    Returns:
        Number of keys deleted

    Example:
        # Invalidate all language cache
        deleted_count = await invalidate_cache("cache:language:*")

        # Invalidate specific method cache
        deleted_count = await invalidate_cache("cache:concept:get_concept_tree:*")

    Note:
        Uses Redis SCAN for safe iteration (doesn't block other operations)
    """
    if not redis_client.client:
        logger.warning("Redis not available, cache invalidation skipped")
        return 0

    try:
        # Find matching keys
        keys = redis_client.keys(pattern)

        if not keys:
            logger.debug(f"No cache keys found matching pattern: {pattern}")
            return 0

        # Delete keys
        deleted = 0
        for key in keys:
            if redis_client.delete(key):
                deleted += 1

        logger.info(
            "Cache invalidated",
            extra={
                "pattern": pattern,
                "deleted_count": deleted,
                "event": "cache_invalidated"
            }
        )

        return deleted

    except Exception as e:
        logger.error(
            "Cache invalidation failed",
            extra={"pattern": pattern, "error": str(e)},
            exc_info=True
        )
        return 0


async def invalidate_cache_key(key: str) -> bool:
    """
    Invalidate (delete) specific cache key.

    Args:
        key: Exact cache key to delete

    Returns:
        True if key was deleted, False otherwise

    Example:
        success = await invalidate_cache_key("cache:language:get_all:d41d8cd98f00b204")
    """
    if not redis_client.client:
        logger.warning("Redis not available, cache invalidation skipped")
        return False

    try:
        success = redis_client.delete(key)

        if success:
            logger.debug(
                "Cache key invalidated",
                extra={"key": key, "event": "cache_key_invalidated"}
            )

        return success

    except Exception as e:
        logger.error(
            "Cache key invalidation failed",
            extra={"key": key, "error": str(e)},
            exc_info=True
        )
        return False


async def clear_all_cache() -> bool:
    """
    Clear ALL cache entries (USE WITH CAUTION!).

    This deletes all keys in the current Redis database.
    Only use for maintenance or testing purposes.

    Returns:
        True if successful, False otherwise

    Example:
        success = await clear_all_cache()

    Warning:
        This operation is destructive and cannot be undone!
        In production, prefer invalidate_cache() with specific patterns.
    """
    if not redis_client.client:
        logger.warning("Redis not available, cache clear skipped")
        return False

    try:
        # Delete only cache keys (not rate limiting, sessions, etc.)
        cache_keys = redis_client.keys("cache:*")

        if not cache_keys:
            logger.info("No cache keys to clear")
            return True

        deleted = 0
        for key in cache_keys:
            if redis_client.delete(key):
                deleted += 1

        logger.warning(
            "All cache cleared",
            extra={
                "deleted_count": deleted,
                "event": "cache_cleared"
            }
        )

        return True

    except Exception as e:
        logger.error(
            "Cache clear failed",
            extra={"error": str(e)},
            exc_info=True
        )
        return False


async def get_cache_stats() -> Dict[str, any]:
    """
    Get cache statistics.

    Returns:
        Dictionary with cache statistics:
        - total_keys: Total number of cache keys
        - keys_by_prefix: Breakdown by key prefix
        - memory_usage: Estimated memory usage (if available)
        - health: Cache health status

    Example:
        stats = await get_cache_stats()
        print(f"Total cache keys: {stats['total_keys']}")
        print(f"Language cache: {stats['keys_by_prefix']['language']}")
    """
    if not redis_client.client:
        return {
            "total_keys": 0,
            "keys_by_prefix": {},
            "memory_usage_bytes": 0,
            "health": "unavailable",
            "error": "Redis not available"
        }

    try:
        # Get all cache keys
        cache_keys = redis_client.keys("cache:*")
        total_keys = len(cache_keys)

        # Group by prefix (e.g., "cache:language:*", "cache:concept:*")
        keys_by_prefix: Dict[str, int] = {}
        for key in cache_keys:
            # Extract prefix: "cache:language:method:hash" -> "language"
            parts = key.split(":")
            if len(parts) >= 2:
                prefix = parts[1]
                keys_by_prefix[prefix] = keys_by_prefix.get(prefix, 0) + 1

        # Check if we're approaching the limit
        health = "healthy"
        if total_keys > MAX_CACHE_KEYS * 0.9:
            health = "warning"
            logger.warning(
                f"Cache keys approaching limit: {total_keys}/{MAX_CACHE_KEYS}"
            )
        elif total_keys > MAX_CACHE_KEYS:
            health = "critical"
            logger.error(
                f"Cache keys exceeded limit: {total_keys}/{MAX_CACHE_KEYS}"
            )

        return {
            "total_keys": total_keys,
            "keys_by_prefix": keys_by_prefix,
            "max_keys": MAX_CACHE_KEYS,
            "health": health
        }

    except Exception as e:
        logger.error(
            "Failed to get cache stats",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            "total_keys": 0,
            "keys_by_prefix": {},
            "max_keys": MAX_CACHE_KEYS,
            "health": "error",
            "error": str(e)
        }


async def get_cache_health() -> Dict[str, any]:
    """
    Check cache health status.

    Returns:
        Dictionary with health information:
        - status: "healthy", "warning", "critical", or "unavailable"
        - available: Whether Redis is available
        - total_keys: Number of cache keys
        - max_keys: Maximum allowed keys
        - usage_percent: Percentage of max keys used

    Example:
        health = await get_cache_health()
        if health["status"] != "healthy":
            logger.warning(f"Cache health: {health['status']}")
    """
    if not redis_client.client:
        return {
            "status": "unavailable",
            "available": False,
            "total_keys": 0,
            "max_keys": MAX_CACHE_KEYS,
            "usage_percent": 0,
            "message": "Redis connection not available"
        }

    try:
        # Test Redis connection
        redis_client.client.ping()

        # Get cache stats
        stats = await get_cache_stats()
        total_keys = stats["total_keys"]

        # Calculate usage percentage
        usage_percent = (total_keys / MAX_CACHE_KEYS * 100) if MAX_CACHE_KEYS > 0 else 0

        # Determine status
        status = "healthy"
        message = "Cache operating normally"

        if usage_percent > 90:
            status = "warning"
            message = f"Cache usage high: {usage_percent:.1f}%"
        elif usage_percent >= 100:
            status = "critical"
            message = f"Cache limit exceeded: {total_keys}/{MAX_CACHE_KEYS} keys"

        return {
            "status": status,
            "available": True,
            "total_keys": total_keys,
            "max_keys": MAX_CACHE_KEYS,
            "usage_percent": round(usage_percent, 2),
            "message": message
        }

    except Exception as e:
        logger.error(
            "Cache health check failed",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            "status": "error",
            "available": False,
            "total_keys": 0,
            "max_keys": MAX_CACHE_KEYS,
            "usage_percent": 0,
            "message": f"Health check failed: {str(e)}"
        }


async def get_cache_keys(pattern: str = "cache:*") -> List[str]:
    """
    Get list of cache keys matching pattern.

    Useful for debugging and cache inspection.

    Args:
        pattern: Redis key pattern (default: "cache:*")

    Returns:
        List of matching cache keys

    Example:
        # Get all language cache keys
        keys = await get_cache_keys("cache:language:*")

        # Get all cache keys
        all_keys = await get_cache_keys()
    """
    if not redis_client.client:
        logger.warning("Redis not available")
        return []

    try:
        keys = redis_client.keys(pattern)
        return keys

    except Exception as e:
        logger.error(
            "Failed to get cache keys",
            extra={"pattern": pattern, "error": str(e)},
            exc_info=True
        )
        return []


# Convenience aliases for common operations
async def invalidate_language_cache() -> int:
    """Invalidate all language-related cache."""
    return await invalidate_cache("cache:language:*")


async def invalidate_concept_cache() -> int:
    """Invalidate all concept-related cache."""
    return await invalidate_cache("cache:concept:*")
