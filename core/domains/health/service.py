from __future__ import annotations

import datetime
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any


def _http_get(url: str, timeout: float = 2.0) -> dict[str, Any]:
    start = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return {
                "status": "healthy",
                "latency_ms": round((time.monotonic() - start) * 1000, 1),
                "http_status": resp.status,
            }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "latency_ms": round((time.monotonic() - start) * 1000, 1),
            "error": str(exc),
        }


class HealthCheckService:
    @staticmethod
    def check_database() -> dict[str, Any]:
        from sqlalchemy import text
        from core.platform.db.database import engine

        start = time.monotonic()
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {
                "status": "healthy",
                "latency_ms": round((time.monotonic() - start) * 1000, 1),
            }
        except Exception as exc:
            return {
                "status": "unhealthy",
                "latency_ms": round((time.monotonic() - start) * 1000, 1),
                "error": str(exc),
            }

    @staticmethod
    def check_redis() -> dict[str, Any]:
        from core.platform.redis.client import redis_client

        start = time.monotonic()
        try:
            ok = redis_client.ping()
            return {
                "status": "healthy" if ok else "unhealthy",
                "latency_ms": round((time.monotonic() - start) * 1000, 1),
                # Различаем настоящий Redis и in-memory fallback
                "backend": "redis" if redis_client.client else "memory",
            }
        except Exception as exc:
            return {
                "status": "unhealthy",
                "latency_ms": round((time.monotonic() - start) * 1000, 1),
                "error": str(exc),
            }

    @staticmethod
    def check_ollama() -> dict[str, Any]:
        host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        result = _http_get(f"{host}/api/tags")
        if result["status"] == "healthy":
            try:
                with urllib.request.urlopen(f"{host}/api/tags", timeout=2.0) as resp:
                    data = json.loads(resp.read())
                    result["models"] = [m["name"] for m in data.get("models", [])]
            except Exception:
                pass
        return result

    @staticmethod
    def check_gateway(host: str) -> dict[str, Any]:
        return _http_get(f"{host}/health")

    @classmethod
    def readiness_check(cls) -> dict[str, Any]:
        """Проверяет только обязательные зависимости (DB + Redis).

        Используется docker-compose для определения готовности контейнера.
        Возвращает 200 / 503.
        """
        db = cls.check_database()
        redis = cls.check_redis()

        all_healthy = db["status"] == "healthy" and redis["status"] == "healthy"
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "services": {"database": db, "redis": redis},
        }

    @classmethod
    def full_check(cls) -> dict[str, Any]:
        """Полная проверка всех сервисов.

        Статусы:
          healthy  — все сервисы в норме
          degraded — обязательные ОК, но опциональные деградированы
          unhealthy — обязательные (DB / Redis) недоступны
        """
        required = {
            "database": cls.check_database(),
            "redis": cls.check_redis(),
        }

        gateway_hosts: dict[str, str] = {
            "chatgpt": os.getenv("GATEWAY_CHATGPT_HOST", "http://gateway-chatgpt:8000"),
            "claude": os.getenv("GATEWAY_CLAUDE_HOST", "http://gateway-claude:8000"),
            "gemini": os.getenv("GATEWAY_GEMINI_HOST", "http://gateway-gemini:8000"),
            "yandexgpt": os.getenv("GATEWAY_YANDEXGPT_HOST", "http://gateway-yandexgpt:8000"),
            "deepseek": os.getenv("GATEWAY_DEEPSEEK_HOST", "http://gateway-deepseek:8000"),
            "local": os.getenv("GATEWAY_LOCAL_HOST", "http://gateway-local:8000"),
        }
        optional: dict[str, Any] = {
            "ollama": cls.check_ollama(),
            "gateways": {
                name: cls.check_gateway(host)
                for name, host in gateway_hosts.items()
            },
        }

        required_ok = all(v["status"] == "healthy" for v in required.values())
        gateways_ok = all(v["status"] == "healthy" for v in optional["gateways"].values())
        ollama_ok = optional["ollama"]["status"] == "healthy"

        if not required_ok:
            overall = "unhealthy"
        elif not (gateways_ok and ollama_ok):
            overall = "degraded"
        else:
            overall = "healthy"

        return {
            "status": overall,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "services": {**required, **optional},
        }
