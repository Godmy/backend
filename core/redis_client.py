"""
Redis client for caching and session management

Used for:
- Email verification tokens
- Password reset tokens
- Session management
- Rate limiting
"""

import os
import redis
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper for application"""

    def __init__(self):
        """Initialize Redis connection"""
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", "6379"))
        self.db = int(os.getenv("REDIS_DB", "0"))
        self.password = os.getenv("REDIS_PASSWORD", None)

        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,  # Automatically decode bytes to strings
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info(f"Redis connected: {self.host}:{self.port}/{self.db}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Don't fail app startup, just log error
            self.client = None

    def set(self, key: str, value: str, expire_seconds: Optional[int] = None) -> bool:
        """
        Set a key-value pair with optional expiration

        Args:
            key: Key name
            value: Value to store
            expire_seconds: Optional TTL in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.warning("Redis not available, skipping set operation")
            return False

        try:
            if expire_seconds:
                return self.client.setex(key, expire_seconds, value)
            else:
                return self.client.set(key, value)
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False

    def get(self, key: str) -> Optional[str]:
        """
        Get value by key

        Args:
            key: Key name

        Returns:
            Value if found, None otherwise
        """
        if not self.client:
            logger.warning("Redis not available, skipping get operation")
            return None

        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """
        Delete a key

        Args:
            key: Key name

        Returns:
            True if deleted, False otherwise
        """
        if not self.client:
            logger.warning("Redis not available, skipping delete operation")
            return False

        try:
            return self.client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists

        Args:
            key: Key name

        Returns:
            True if exists, False otherwise
        """
        if not self.client:
            return False

        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False

    def ttl(self, key: str) -> int:
        """
        Get remaining TTL for key

        Args:
            key: Key name

        Returns:
            Remaining seconds, -1 if no expiry, -2 if not found
        """
        if not self.client:
            return -2

        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error for key {key}: {e}")
            return -2

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter

        Args:
            key: Key name
            amount: Amount to increment

        Returns:
            New value after increment, None on error
        """
        if not self.client:
            return None

        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error for key {key}: {e}")
            return None

    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration for existing key

        Args:
            key: Key name
            seconds: TTL in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            return self.client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False

    def keys(self, pattern: str) -> list:
        """
        Find keys matching pattern

        Args:
            pattern: Pattern to match (e.g., "user:*")

        Returns:
            List of matching keys
        """
        if not self.client:
            return []

        try:
            return self.client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis KEYS error for pattern {pattern}: {e}")
            return []

    def flushdb(self) -> bool:
        """
        Clear all keys in current database (USE WITH CAUTION!)

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            self.client.flushdb()
            logger.warning("Redis database flushed!")
            return True
        except Exception as e:
            logger.error(f"Redis FLUSHDB error: {e}")
            return False


# Singleton instance
redis_client = RedisClient()
