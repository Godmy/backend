from __future__ import annotations

import functools
import hashlib
import json
from typing import Any, Callable

from core.platform.redis.client import redis_client


def _to_serializable(value: Any):
    if hasattr(value, "__table__"):
        return {
            column.name: getattr(value, column.name)
            for column in value.__table__.columns
        }
    if isinstance(value, (list, tuple)):
        return [_to_serializable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_serializable(item) for key, item in value.items()}
    return value


def _serialize_value(value: Any) -> str:
    return json.dumps(_to_serializable(value), default=str, ensure_ascii=False)


def _deserialize_value(value: str):
    return json.loads(value)


def _generate_cache_key(
    key_prefix: str,
    method_name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    key_builder: Callable[[tuple[Any, ...], dict[str, Any]], str] | None = None,
) -> str:
    effective_args = args[1:] if args and hasattr(args[0], "__class__") else args
    if key_builder is not None:
        suffix = key_builder(effective_args, kwargs)
        return f"cache:{key_prefix}:{method_name}:{suffix}"

    payload = json.dumps(
        {"args": _to_serializable(effective_args), "kwargs": _to_serializable(kwargs)},
        sort_keys=True,
        default=str,
        ensure_ascii=False,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"cache:{key_prefix}:{method_name}:{digest}"


def cached(
    key_prefix: str,
    ttl: int = 300,
    cache_none: bool = False,
    key_builder: Callable[[tuple[Any, ...], dict[str, Any]], str] | None = None,
):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = _generate_cache_key(
                key_prefix,
                func.__name__,
                args,
                kwargs,
                key_builder=key_builder,
            )
            try:
                cached_value = redis_client.get(cache_key)
                if cached_value is not None:
                    return _deserialize_value(cached_value)
            except Exception:
                pass

            result = await func(*args, **kwargs)
            if result is None and not cache_none:
                return result

            try:
                redis_client.set(
                    cache_key,
                    _serialize_value(result),
                    expire_seconds=ttl,
                )
            except Exception:
                pass
            return result

        return wrapper

    return decorator

