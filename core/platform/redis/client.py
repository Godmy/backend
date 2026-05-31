from __future__ import annotations

import fnmatch
import time

try:
    import redis as redis_lib
except Exception:  # pragma: no cover
    redis_lib = None


class RedisClient:
    def __init__(self) -> None:
        self.client = None
        self._memory_store: dict[str, tuple[str, float | None]] = {}
        self._connect()

    def _connect(self) -> None:
        if redis_lib is None:
            return
        try:
            self.client = redis_lib.Redis(
                host="redis",
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            self.client.ping()
        except Exception:
            self.client = None

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [
            key for key, (_, expires_at) in self._memory_store.items()
            if expires_at is not None and expires_at <= now
        ]
        for key in expired:
            self._memory_store.pop(key, None)

    def get(self, key: str):
        if self.client:
            try:
                return self.client.get(key)
            except Exception:
                pass
        self._purge_expired()
        item = self._memory_store.get(key)
        return None if item is None else item[0]

    def set(self, key: str, value: str, expire_seconds: int | None = None) -> bool:
        if self.client:
            try:
                return bool(self.client.set(key, value, ex=expire_seconds))
            except Exception:
                pass
        expires_at = None if expire_seconds is None else time.time() + expire_seconds
        self._memory_store[key] = (value, expires_at)
        return True

    def delete(self, key: str) -> int:
        if self.client:
            try:
                return int(self.client.delete(key))
            except Exception:
                pass
        return 1 if self._memory_store.pop(key, None) is not None else 0

    def incr(self, key: str) -> int:
        if self.client:
            try:
                return int(self.client.incr(key))
            except Exception:
                pass
        current = int(self.get(key) or "0") + 1
        ttl = self.ttl(key)
        self.set(key, str(current), expire_seconds=None if ttl < 0 else ttl)
        return current

    def ttl(self, key: str) -> int:
        if self.client:
            try:
                return int(self.client.ttl(key))
            except Exception:
                pass
        self._purge_expired()
        item = self._memory_store.get(key)
        if item is None:
            return -2
        _, expires_at = item
        if expires_at is None:
            return -1
        return max(0, int(expires_at - time.time()))

    def keys(self, pattern: str):
        if self.client:
            try:
                return list(self.client.keys(pattern))
            except Exception:
                pass
        self._purge_expired()
        return [key for key in self._memory_store if fnmatch.fnmatch(key, pattern)]

    def ping(self) -> bool:
        if self.client:
            try:
                return bool(self.client.ping())
            except Exception:
                return False
        return True


redis_client = RedisClient()

