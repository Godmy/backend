"""
Redis-based caching decorator for service methods.

Provides transparent caching for expensive or frequently accessed operations with:
- Automatic key generation from function name and arguments
- TTL-based expiration
- JSON serialization for complex objects
- Graceful fallback on Redis failure
- Prometheus metrics for cache hits/misses/errors
- Structured logging

Implementation for User Story #3 - Redis Service-Level Caching (P2)

Usage:
    @cached(key_prefix="language:list", ttl=3600)
    def get_all_languages(self) -> List[LanguageModel]:
        return self.db.query(LanguageModel).all()

    @cached(key_prefix="concept:tree", ttl=300, cache_none=False)
    def get_concept_tree(self, parent_id: Optional[int] = None):
        # Expensive tree query...
        return tree_data
"""

import functools
import hashlib
import json
import os
from typing import Any, Callable, Optional, TypeVar, cast

from core.redis_client import redis_client
from core.structured_logging import get_logger

logger = get_logger(__name__)

# Type variable for decorated function
F = TypeVar("F", bound=Callable[..., Any])

# Configuration from environment
CACHE_ENABLED = os.getenv("SERVICE_CACHE_ENABLED", "true").lower() == "true"
DEFAULT_TTL = int(os.getenv("SERVICE_CACHE_DEFAULT_TTL", "300"))

# Try to import Prometheus metrics
try:
    from prometheus_client import Counter

    cache_hits_counter = Counter(
        "service_cache_hits_total",
        "Total number of cache hits",
        ["service", "method"]
    )
    cache_misses_counter = Counter(
        "service_cache_misses_total",
        "Total number of cache misses",
        ["service", "method"]
    )
    cache_errors_counter = Counter(
        "service_cache_errors_total",
        "Total number of cache errors",
        ["service", "method", "error_type"]
    )
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False
    logger.warning("Prometheus metrics not available for caching")


def _serialize_value(value: Any) -> str:
    """
    Serialize value to JSON string for caching.

    Handles:
    - Pydantic models (via model_dump())
    - SQLAlchemy models (via __dict__)
    - Lists/dicts of models
    - Primitive types

    Args:
        value: Value to serialize

    Returns:
        JSON string representation

    Raises:
        TypeError: If value is not serializable
    """
    def _convert_to_dict(obj: Any) -> Any:
        """Convert object to JSON-serializable dict"""
        # Handle None
        if obj is None:
            return None

        # Handle primitives
        if isinstance(obj, (str, int, float, bool)):
            return obj

        # Handle lists
        if isinstance(obj, list):
            return [_convert_to_dict(item) for item in obj]

        # Handle dicts
        if isinstance(obj, dict):
            return {key: _convert_to_dict(val) for key, val in obj.items()}

        # Handle Pydantic models
        if hasattr(obj, "model_dump"):
            return obj.model_dump()

        # Handle SQLAlchemy models
        if hasattr(obj, "__dict__") and hasattr(obj, "__table__"):
            # SQLAlchemy model
            data = {}
            for column in obj.__table__.columns:
                value = getattr(obj, column.name, None)
                # Skip complex relationships
                if not isinstance(value, (str, int, float, bool, type(None))):
                    continue
                data[column.name] = value
            return data

        # Handle other objects with __dict__
        if hasattr(obj, "__dict__"):
            return {
                key: _convert_to_dict(val)
                for key, val in obj.__dict__.items()
                if not key.startswith("_")
            }

        # Fallback: convert to string
        return str(obj)

    try:
        serializable_value = _convert_to_dict(value)
        return json.dumps(serializable_value, ensure_ascii=False, default=str)
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize value for caching: {e}")
        raise


def _deserialize_value(json_str: str) -> Any:
    """
    Deserialize JSON string back to Python object.

    Note: Returns plain dict/list structures, not original model instances.
    This is acceptable for read-only cached data.

    Args:
        json_str: JSON string

    Returns:
        Deserialized Python object

    Raises:
        ValueError: If JSON is invalid
    """
    try:
        return json.loads(json_str)
    except (TypeError, ValueError, json.JSONDecodeError) as e:
        logger.error(f"Failed to deserialize cached value: {e}")
        raise


def _generate_cache_key(
    key_prefix: str,
    func_name: str,
    args: tuple,
    kwargs: dict,
    key_builder: Optional[Callable] = None
) -> str:
    """
    Generate cache key from function name and arguments.

    Format: cache:{key_prefix}:{func_name}:{args_hash}

    Args:
        key_prefix: Prefix for cache key (e.g., "language:list")
        func_name: Function name
        args: Positional arguments (excluding 'self')
        kwargs: Keyword arguments
        key_builder: Optional custom key builder function

    Returns:
        Cache key string

    Example:
        cache:language:list:d41d8cd98f00b204e9800998ecf8427e
    """
    if key_builder:
        # Use custom key builder
        custom_key = key_builder(args, kwargs)
        return f"cache:{key_prefix}:{func_name}:{custom_key}"

    # Default: hash arguments
    # Create deterministic representation of args and kwargs
    args_repr = json.dumps(
        {"args": args, "kwargs": kwargs},
        sort_keys=True,
        default=str
    )

    # Generate MD5 hash of arguments
    args_hash = hashlib.md5(args_repr.encode()).hexdigest()

    return f"cache:{key_prefix}:{func_name}:{args_hash}"


def cached(
    key_prefix: str,
    ttl: int = DEFAULT_TTL,
    cache_none: bool = False,
    key_builder: Optional[Callable] = None
) -> Callable[[F], F]:
    """
    Decorator for caching service method results in Redis.

    Features:
    - Transparent caching with automatic key generation
    - TTL-based expiration
    - JSON serialization for complex objects (Pydantic, SQLAlchemy models)
    - Graceful fallback on Redis failure (fail-open)
    - Prometheus metrics (hits, misses, errors)
    - Structured logging
    - Can be disabled via SERVICE_CACHE_ENABLED=false env var

    Args:
        key_prefix: Prefix for cache keys (e.g., "language:list", "concept:tree")
        ttl: Time-to-live in seconds (default: SERVICE_CACHE_DEFAULT_TTL or 300)
        cache_none: Whether to cache None results (default: False)
        key_builder: Optional custom function to build cache key from (args, kwargs)

    Returns:
        Decorated function with caching

    Example:
        @cached(key_prefix="language:list", ttl=3600)
        def get_all_languages(self) -> List[LanguageModel]:
            return self.db.query(LanguageModel).all()

        @cached(key_prefix="concept:tree", ttl=300, cache_none=False)
        def get_concept_tree(self, parent_id: Optional[int] = None):
            # ...complex query...
            return tree

        @cached(
            key_prefix="user:profile",
            ttl=600,
            key_builder=lambda args, kwargs: f"user_{kwargs.get('user_id', args[0])}"
        )
        def get_user_profile(self, user_id: int):
            return self.db.query(User).filter(User.id == user_id).first()

    Notes:
    - Only works with async functions (returns awaitable)
    - First argument is assumed to be 'self' and excluded from cache key
    - If Redis is unavailable, function executes normally (fail-open)
    - Cached values are returned as dicts/lists, not original model instances
    - For mutation operations, use invalidate_cache() to clear related cache
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip caching if disabled
            if not CACHE_ENABLED:
                return await func(*args, **kwargs)

            # Extract service and method names for metrics
            service_name = key_prefix.split(":")[0] if ":" in key_prefix else key_prefix
            method_name = func.__name__

            # Generate cache key (exclude 'self' from args)
            func_args = args[1:] if args and hasattr(args[0], "__class__") else args
            cache_key = _generate_cache_key(
                key_prefix=key_prefix,
                func_name=method_name,
                args=func_args,
                kwargs=kwargs,
                key_builder=key_builder
            )

            # Try to get from cache
            try:
                cached_value = redis_client.get(cache_key)

                if cached_value is not None:
                    # Cache hit
                    logger.debug(
                        "Cache hit",
                        extra={
                            "service": service_name,
                            "method": method_name,
                            "cache_key": cache_key,
                            "event": "cache_hit"
                        }
                    )

                    if METRICS_ENABLED:
                        cache_hits_counter.labels(
                            service=service_name,
                            method=method_name
                        ).inc()

                    # Deserialize and return
                    try:
                        return _deserialize_value(cached_value)
                    except (ValueError, json.JSONDecodeError) as e:
                        # If deserialization fails, log error and fetch fresh data
                        logger.warning(
                            "Cache deserialization failed, fetching fresh data",
                            extra={
                                "service": service_name,
                                "method": method_name,
                                "cache_key": cache_key,
                                "error": str(e)
                            }
                        )
                        if METRICS_ENABLED:
                            cache_errors_counter.labels(
                                service=service_name,
                                method=method_name,
                                error_type="deserialization_error"
                            ).inc()

            except Exception as e:
                # Redis error, log and continue
                logger.warning(
                    "Cache read error, fetching fresh data",
                    extra={
                        "service": service_name,
                        "method": method_name,
                        "cache_key": cache_key,
                        "error": str(e)
                    }
                )
                if METRICS_ENABLED:
                    cache_errors_counter.labels(
                        service=service_name,
                        method=method_name,
                        error_type="redis_error"
                    ).inc()

            # Cache miss - execute function
            logger.debug(
                "Cache miss",
                extra={
                    "service": service_name,
                    "method": method_name,
                    "cache_key": cache_key,
                    "event": "cache_miss"
                }
            )

            if METRICS_ENABLED:
                cache_misses_counter.labels(
                    service=service_name,
                    method=method_name
                ).inc()

            # Execute original function
            result = await func(*args, **kwargs)

            # Cache result if not None (or if cache_none=True)
            if result is not None or cache_none:
                try:
                    # Serialize result
                    serialized_result = _serialize_value(result)

                    # Store in Redis with TTL
                    success = redis_client.set(cache_key, serialized_result, expire_seconds=ttl)

                    if success:
                        logger.debug(
                            "Cached result",
                            extra={
                                "service": service_name,
                                "method": method_name,
                                "cache_key": cache_key,
                                "ttl": ttl,
                                "event": "cache_set"
                            }
                        )
                    else:
                        logger.warning(
                            "Failed to cache result",
                            extra={
                                "service": service_name,
                                "method": method_name,
                                "cache_key": cache_key
                            }
                        )

                except (TypeError, ValueError) as e:
                    # Serialization error - log but don't fail
                    logger.warning(
                        "Failed to serialize result for caching",
                        extra={
                            "service": service_name,
                            "method": method_name,
                            "cache_key": cache_key,
                            "error": str(e)
                        }
                    )
                    if METRICS_ENABLED:
                        cache_errors_counter.labels(
                            service=service_name,
                            method=method_name,
                            error_type="serialization_error"
                        ).inc()

            return result

        return cast(F, wrapper)

    return decorator
