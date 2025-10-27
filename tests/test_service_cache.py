"""
Comprehensive tests for Redis service-level caching.

Tests:
- Cache decorator functionality
- Cache invalidation
- Redis failure scenarios (graceful fallback)
- Serialization/deserialization
- TTL expiration
- Cache statistics
- Performance improvements

Implementation for User Story #3 - Redis Service-Level Caching (P2)
"""

import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock

import pytest
from sqlalchemy.orm import Session

from core.decorators.cache import cached, _serialize_value, _deserialize_value, _generate_cache_key
from core.services.cache_service import (
    invalidate_cache,
    invalidate_cache_key,
    clear_all_cache,
    get_cache_stats,
    get_cache_health,
    get_cache_keys,
    invalidate_language_cache,
    invalidate_concept_cache
)
from core.redis_client import redis_client
from languages.models.language import LanguageModel
from languages.services.language_service import LanguageService
from languages.services.concept_service import ConceptService


@pytest.fixture(autouse=True)
def clear_cache_before_test():
    """Clear all cache before each test"""
    if redis_client.client:
        # Clear only cache keys, not other Redis data
        cache_keys = redis_client.keys("cache:*")
        for key in cache_keys:
            redis_client.delete(key)
    yield
    # Clear again after test
    if redis_client.client:
        cache_keys = redis_client.keys("cache:*")
        for key in cache_keys:
            redis_client.delete(key)


# ==============================================================================
# Unit Tests - Serialization
# ==============================================================================


def test_serialize_primitive_types():
    """Test serialization of primitive types"""
    assert _serialize_value(None) == "null"
    assert _serialize_value(42) == "42"
    assert _serialize_value(3.14) == "3.14"
    assert _serialize_value("hello") == '"hello"'
    assert _serialize_value(True) == "true"
    assert _serialize_value(False) == "false"


def test_serialize_list():
    """Test serialization of lists"""
    data = [1, 2, 3, "hello", True]
    serialized = _serialize_value(data)
    deserialized = json.loads(serialized)
    assert deserialized == [1, 2, 3, "hello", True]


def test_serialize_dict():
    """Test serialization of dictionaries"""
    data = {"name": "test", "count": 42, "active": True}
    serialized = _serialize_value(data)
    deserialized = json.loads(serialized)
    assert deserialized == data


def test_serialize_sqlalchemy_model():
    """Test serialization of SQLAlchemy models"""
    # Create a mock language model
    language = LanguageModel(id=1, code="en", name="English")

    serialized = _serialize_value(language)
    deserialized = json.loads(serialized)

    assert deserialized["id"] == 1
    assert deserialized["code"] == "en"
    assert deserialized["name"] == "English"


def test_serialize_list_of_models():
    """Test serialization of lists of SQLAlchemy models"""
    languages = [
        LanguageModel(id=1, code="en", name="English"),
        LanguageModel(id=2, code="ru", name="Russian"),
    ]

    serialized = _serialize_value(languages)
    deserialized = json.loads(serialized)

    assert len(deserialized) == 2
    assert deserialized[0]["code"] == "en"
    assert deserialized[1]["code"] == "ru"


def test_deserialize_value():
    """Test deserialization of JSON strings"""
    assert _deserialize_value("null") is None
    assert _deserialize_value("42") == 42
    assert _deserialize_value('"hello"') == "hello"
    assert _deserialize_value("[1, 2, 3]") == [1, 2, 3]
    assert _deserialize_value('{"name": "test"}') == {"name": "test"}


def test_deserialize_invalid_json():
    """Test deserialization handles invalid JSON"""
    with pytest.raises((ValueError, json.JSONDecodeError)):
        _deserialize_value("invalid json{")


# ==============================================================================
# Unit Tests - Cache Key Generation
# ==============================================================================


def test_generate_cache_key_no_args():
    """Test cache key generation without arguments"""
    key = _generate_cache_key("language:list", "get_all", (), {})
    assert key.startswith("cache:language:list:get_all:")
    assert len(key) > len("cache:language:list:get_all:")


def test_generate_cache_key_with_args():
    """Test cache key generation with arguments"""
    key1 = _generate_cache_key("user:profile", "get_user", (123,), {})
    key2 = _generate_cache_key("user:profile", "get_user", (456,), {})

    # Different args should produce different keys
    assert key1 != key2
    assert key1.startswith("cache:user:profile:get_user:")
    assert key2.startswith("cache:user:profile:get_user:")


def test_generate_cache_key_with_kwargs():
    """Test cache key generation with keyword arguments"""
    key1 = _generate_cache_key("user:profile", "get_user", (), {"user_id": 123})
    key2 = _generate_cache_key("user:profile", "get_user", (), {"user_id": 456})

    # Different kwargs should produce different keys
    assert key1 != key2


def test_generate_cache_key_deterministic():
    """Test that same arguments always produce the same key"""
    key1 = _generate_cache_key("test", "method", (1, 2), {"key": "value"})
    key2 = _generate_cache_key("test", "method", (1, 2), {"key": "value"})

    assert key1 == key2


def test_generate_cache_key_custom_builder():
    """Test custom key builder function"""
    def custom_builder(args, kwargs):
        return f"user_{kwargs.get('user_id', args[0])}"

    key = _generate_cache_key(
        "user:profile",
        "get_user",
        (),
        {"user_id": 123},
        key_builder=custom_builder
    )

    assert key == "cache:user:profile:get_user:user_123"


# ==============================================================================
# Integration Tests - Cache Decorator
# ==============================================================================


@pytest.mark.asyncio
async def test_cached_decorator_basic():
    """Test basic caching functionality"""
    call_count = 0

    class TestService:
        @cached(key_prefix="test:basic", ttl=60)
        async def get_data(self):
            nonlocal call_count
            call_count += 1
            return {"value": 42}

    service = TestService()

    # First call - should execute function
    result1 = await service.get_data()
    assert result1 == {"value": 42}
    assert call_count == 1

    # Second call - should return cached value
    result2 = await service.get_data()
    assert result2 == {"value": 42}
    assert call_count == 1  # Function not called again

    # Verify cache hit
    assert result1 == result2


@pytest.mark.asyncio
async def test_cached_decorator_with_args():
    """Test caching with different arguments"""
    call_count = {}

    class TestService:
        @cached(key_prefix="test:args", ttl=60)
        async def get_data(self, id: int):
            nonlocal call_count
            call_count[id] = call_count.get(id, 0) + 1
            return {"id": id, "value": id * 10}

    service = TestService()

    # Call with id=1
    result1 = await service.get_data(1)
    assert result1 == {"id": 1, "value": 10}
    assert call_count[1] == 1

    # Call again with id=1 - should be cached
    result1_cached = await service.get_data(1)
    assert result1_cached == {"id": 1, "value": 10}
    assert call_count[1] == 1  # Not called again

    # Call with id=2 - different cache key
    result2 = await service.get_data(2)
    assert result2 == {"id": 2, "value": 20}
    assert call_count[2] == 1


@pytest.mark.asyncio
async def test_cached_decorator_cache_none():
    """Test caching of None values"""
    call_count = 0

    class TestService:
        @cached(key_prefix="test:none", ttl=60, cache_none=True)
        async def get_data(self):
            nonlocal call_count
            call_count += 1
            return None

    service = TestService()

    # First call
    result1 = await service.get_data()
    assert result1 is None
    assert call_count == 1

    # Second call - None should be cached
    result2 = await service.get_data()
    assert result2 is None
    assert call_count == 1  # Function not called again


@pytest.mark.asyncio
async def test_cached_decorator_no_cache_none():
    """Test that None values are not cached by default"""
    call_count = 0

    class TestService:
        @cached(key_prefix="test:no_none", ttl=60, cache_none=False)
        async def get_data(self):
            nonlocal call_count
            call_count += 1
            return None

    service = TestService()

    # First call
    result1 = await service.get_data()
    assert result1 is None
    assert call_count == 1

    # Second call - None not cached, function called again
    result2 = await service.get_data()
    assert result2 is None
    assert call_count == 2


@pytest.mark.asyncio
async def test_cached_decorator_ttl_expiration():
    """Test that cache expires after TTL"""
    if not redis_client.client:
        pytest.skip("Redis not available")

    call_count = 0

    class TestService:
        @cached(key_prefix="test:ttl", ttl=1)  # 1 second TTL
        async def get_data(self):
            nonlocal call_count
            call_count += 1
            return {"value": call_count}

    service = TestService()

    # First call
    result1 = await service.get_data()
    assert result1 == {"value": 1}
    assert call_count == 1

    # Immediate second call - should be cached
    result2 = await service.get_data()
    assert result2 == {"value": 1}
    assert call_count == 1

    # Wait for TTL to expire
    await asyncio.sleep(1.5)

    # Third call after expiration - should execute function again
    result3 = await service.get_data()
    assert result3 == {"value": 2}
    assert call_count == 2


# ==============================================================================
# Integration Tests - Language Service Caching
# ==============================================================================


@pytest.mark.asyncio
async def test_language_service_get_all_caching(db: Session):
    """Test that language_service.get_all() uses caching"""
    service = LanguageService(db)

    # First call - should execute query
    languages1 = await service.get_all()
    assert len(languages1) > 0

    # Second call - should return cached result
    languages2 = await service.get_all()
    assert len(languages2) == len(languages1)

    # Verify cache key exists
    cache_keys = redis_client.keys("cache:language:list:*")
    assert len(cache_keys) > 0


@pytest.mark.asyncio
async def test_language_service_cache_invalidation(db: Session):
    """Test that language mutations invalidate cache"""
    service = LanguageService(db)

    # Get initial languages (populates cache)
    languages_before = await service.get_all()
    initial_count = len(languages_before)

    # Create new language
    new_language = await service.create(code="test_cache", name="Test Cache Language")
    assert new_language.id is not None

    # Cache should be invalidated, get_all should return fresh data
    languages_after = await service.get_all()
    assert len(languages_after) == initial_count + 1

    # Clean up
    await service.delete(new_language.id)


# ==============================================================================
# Integration Tests - Concept Service Caching
# ==============================================================================


@pytest.mark.asyncio
async def test_concept_service_get_all_caching(db: Session):
    """Test that concept_service.get_all() uses caching"""
    service = ConceptService(db)

    # First call - should execute query
    concepts1 = await service.get_all()
    initial_count = len(concepts1)

    # Second call - should return cached result
    concepts2 = await service.get_all()
    assert len(concepts2) == initial_count

    # Verify cache key exists
    cache_keys = redis_client.keys("cache:concept:list:*")
    assert len(cache_keys) > 0


@pytest.mark.asyncio
async def test_concept_service_cache_invalidation(db: Session):
    """Test that concept mutations invalidate cache"""
    service = ConceptService(db)

    # Get initial concepts (populates cache)
    concepts_before = await service.get_all()
    initial_count = len(concepts_before)

    # Create new concept
    new_concept = await service.create(path="/test_cache/", depth=1, parent_id=None)
    assert new_concept.id is not None

    # Cache should be invalidated, get_all should return fresh data
    concepts_after = await service.get_all()
    assert len(concepts_after) == initial_count + 1

    # Clean up
    await service.delete(new_concept.id)


# ==============================================================================
# Integration Tests - Cache Service Utilities
# ==============================================================================


@pytest.mark.asyncio
async def test_invalidate_cache_pattern():
    """Test cache invalidation by pattern"""
    if not redis_client.client:
        pytest.skip("Redis not available")

    # Set some test cache values
    redis_client.set("cache:language:get_all:abc123", '{"data": 1}', expire_seconds=300)
    redis_client.set("cache:language:get_by_id:def456", '{"data": 2}', expire_seconds=300)
    redis_client.set("cache:concept:get_all:ghi789", '{"data": 3}', expire_seconds=300)

    # Invalidate all language cache
    deleted_count = await invalidate_cache("cache:language:*")
    assert deleted_count == 2

    # Verify language cache deleted but concept cache remains
    language_keys = redis_client.keys("cache:language:*")
    concept_keys = redis_client.keys("cache:concept:*")
    assert len(language_keys) == 0
    assert len(concept_keys) == 1


@pytest.mark.asyncio
async def test_invalidate_cache_key():
    """Test cache invalidation by specific key"""
    if not redis_client.client:
        pytest.skip("Redis not available")

    # Set a test cache value
    test_key = "cache:test:key:123"
    redis_client.set(test_key, '{"data": 1}', expire_seconds=300)

    # Verify it exists
    assert redis_client.exists(test_key)

    # Invalidate specific key
    success = await invalidate_cache_key(test_key)
    assert success is True

    # Verify it's deleted
    assert not redis_client.exists(test_key)


@pytest.mark.asyncio
async def test_clear_all_cache():
    """Test clearing all cache"""
    if not redis_client.client:
        pytest.skip("Redis not available")

    # Set multiple cache values
    redis_client.set("cache:test:1", '{"data": 1}', expire_seconds=300)
    redis_client.set("cache:test:2", '{"data": 2}', expire_seconds=300)
    redis_client.set("cache:test:3", '{"data": 3}', expire_seconds=300)

    # Clear all cache
    success = await clear_all_cache()
    assert success is True

    # Verify all cache cleared
    cache_keys = redis_client.keys("cache:*")
    assert len(cache_keys) == 0


@pytest.mark.asyncio
async def test_get_cache_stats():
    """Test getting cache statistics"""
    if not redis_client.client:
        pytest.skip("Redis not available")

    # Set some test cache values
    redis_client.set("cache:language:get_all:abc", '{"data": 1}', expire_seconds=300)
    redis_client.set("cache:language:get_by_id:def", '{"data": 2}', expire_seconds=300)
    redis_client.set("cache:concept:get_all:ghi", '{"data": 3}', expire_seconds=300)

    # Get stats
    stats = await get_cache_stats()

    assert stats["total_keys"] == 3
    assert "language" in stats["keys_by_prefix"]
    assert "concept" in stats["keys_by_prefix"]
    assert stats["keys_by_prefix"]["language"] == 2
    assert stats["keys_by_prefix"]["concept"] == 1
    assert stats["health"] in ["healthy", "warning", "critical"]


@pytest.mark.asyncio
async def test_get_cache_health():
    """Test getting cache health status"""
    health = await get_cache_health()

    assert "status" in health
    assert "available" in health
    assert "total_keys" in health
    assert "max_keys" in health
    assert "usage_percent" in health

    if redis_client.client:
        assert health["available"] is True
        assert health["status"] in ["healthy", "warning", "critical", "error"]
    else:
        assert health["available"] is False
        assert health["status"] == "unavailable"


@pytest.mark.asyncio
async def test_get_cache_keys():
    """Test getting cache keys by pattern"""
    if not redis_client.client:
        pytest.skip("Redis not available")

    # Set some test cache values
    redis_client.set("cache:language:get_all:abc", '{"data": 1}', expire_seconds=300)
    redis_client.set("cache:concept:get_all:def", '{"data": 2}', expire_seconds=300)

    # Get all cache keys
    all_keys = await get_cache_keys("cache:*")
    assert len(all_keys) >= 2

    # Get language cache keys only
    language_keys = await get_cache_keys("cache:language:*")
    assert len(language_keys) >= 1


@pytest.mark.asyncio
async def test_invalidate_language_cache():
    """Test language cache invalidation convenience function"""
    if not redis_client.client:
        pytest.skip("Redis not available")

    # Set some test cache values
    redis_client.set("cache:language:get_all:abc", '{"data": 1}', expire_seconds=300)
    redis_client.set("cache:language:get_by_id:def", '{"data": 2}', expire_seconds=300)
    redis_client.set("cache:concept:get_all:ghi", '{"data": 3}', expire_seconds=300)

    # Invalidate language cache
    deleted_count = await invalidate_language_cache()
    assert deleted_count == 2

    # Verify only language cache deleted
    language_keys = redis_client.keys("cache:language:*")
    concept_keys = redis_client.keys("cache:concept:*")
    assert len(language_keys) == 0
    assert len(concept_keys) == 1


@pytest.mark.asyncio
async def test_invalidate_concept_cache():
    """Test concept cache invalidation convenience function"""
    if not redis_client.client:
        pytest.skip("Redis not available")

    # Set some test cache values
    redis_client.set("cache:language:get_all:abc", '{"data": 1}', expire_seconds=300)
    redis_client.set("cache:concept:get_all:def", '{"data": 2}', expire_seconds=300)
    redis_client.set("cache:concept:get_tree:ghi", '{"data": 3}', expire_seconds=300)

    # Invalidate concept cache
    deleted_count = await invalidate_concept_cache()
    assert deleted_count == 2

    # Verify only concept cache deleted
    language_keys = redis_client.keys("cache:language:*")
    concept_keys = redis_client.keys("cache:concept:*")
    assert len(language_keys) == 1
    assert len(concept_keys) == 0


# ==============================================================================
# Integration Tests - Redis Failure Scenarios
# ==============================================================================


@pytest.mark.asyncio
async def test_cache_graceful_fallback_on_redis_failure():
    """Test that functions work normally when Redis is unavailable"""
    call_count = 0

    class TestService:
        @cached(key_prefix="test:fallback", ttl=60)
        async def get_data(self):
            nonlocal call_count
            call_count += 1
            return {"value": 42}

    service = TestService()

    # Mock Redis client as None (simulating unavailability)
    with patch('core.decorators.cache.redis_client.client', None):
        # First call - function should execute
        result1 = await service.get_data()
        assert result1 == {"value": 42}
        assert call_count == 1

        # Second call - function should execute again (no caching)
        result2 = await service.get_data()
        assert result2 == {"value": 42}
        assert call_count == 2


@pytest.mark.asyncio
async def test_cache_handles_redis_errors():
    """Test that cache decorator handles Redis errors gracefully"""
    call_count = 0

    class TestService:
        @cached(key_prefix="test:error", ttl=60)
        async def get_data(self):
            nonlocal call_count
            call_count += 1
            return {"value": 42}

    service = TestService()

    # Mock Redis to raise exceptions
    with patch.object(redis_client, 'get', side_effect=Exception("Redis error")):
        with patch.object(redis_client, 'set', side_effect=Exception("Redis error")):
            # Function should still work, just without caching
            result = await service.get_data()
            assert result == {"value": 42}
            assert call_count == 1


# ==============================================================================
# Performance Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_cache_performance_improvement():
    """Test that caching provides performance improvement"""
    if not redis_client.client:
        pytest.skip("Redis not available")

    class TestService:
        @cached(key_prefix="test:perf", ttl=60)
        async def slow_operation(self):
            # Simulate expensive operation
            await asyncio.sleep(0.1)
            return {"result": "data"}

    service = TestService()

    # Measure first call (uncached)
    start1 = time.time()
    result1 = await service.slow_operation()
    duration1 = time.time() - start1

    assert result1 == {"result": "data"}
    assert duration1 >= 0.1  # Should take at least 100ms

    # Measure second call (cached)
    start2 = time.time()
    result2 = await service.slow_operation()
    duration2 = time.time() - start2

    assert result2 == {"result": "data"}
    assert duration2 < 0.05  # Should be much faster (< 50ms)

    # Cached call should be significantly faster
    improvement_ratio = duration1 / duration2
    assert improvement_ratio > 2  # At least 2x faster


@pytest.mark.asyncio
async def test_cache_disabled_via_env():
    """Test that caching can be disabled via environment variable"""
    call_count = 0

    class TestService:
        @cached(key_prefix="test:disabled", ttl=60)
        async def get_data(self):
            nonlocal call_count
            call_count += 1
            return {"value": 42}

    service = TestService()

    # Disable caching via environment
    with patch('core.decorators.cache.CACHE_ENABLED', False):
        # First call
        result1 = await service.get_data()
        assert result1 == {"value": 42}
        assert call_count == 1

        # Second call - should execute again (caching disabled)
        result2 = await service.get_data()
        assert result2 == {"value": 42}
        assert call_count == 2
