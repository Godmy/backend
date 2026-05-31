from __future__ import annotations

from core.platform.redis.client import redis_client


async def invalidate_cache(prefix: str) -> int:
    keys = redis_client.keys(f"cache:{prefix}*")
    for key in keys:
        redis_client.delete(key)
    return len(keys)


async def invalidate_cache_key(key: str) -> bool:
    return bool(redis_client.delete(key))


async def clear_all_cache() -> int:
    keys = redis_client.keys("cache:*")
    for key in keys:
        redis_client.delete(key)
    return len(keys)


async def get_cache_keys(pattern: str = "cache:*") -> list[str]:
    return list(redis_client.keys(pattern))


async def get_cache_stats() -> dict[str, int]:
    keys = redis_client.keys("cache:*")
    return {"total_keys": len(keys)}


async def get_cache_health() -> dict[str, bool]:
    return {"healthy": redis_client.ping()}


async def invalidate_language_cache() -> int:
    return await invalidate_cache("language:")


async def invalidate_concept_cache() -> int:
    return await invalidate_cache("concept:")
