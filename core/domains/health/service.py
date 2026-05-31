from __future__ import annotations

from sqlalchemy import text

from core.platform.celery.app import celery_app
from core.platform.db.database import engine
from core.platform.redis.client import redis_client


class HealthCheckService:
    @staticmethod
    def check_database() -> dict[str, object]:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return {"status": "healthy"}
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}

    @staticmethod
    def check_redis() -> dict[str, object]:
        try:
            redis_client.ping()
            return {"status": "healthy"}
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}

    @staticmethod
    def check_celery() -> dict[str, object]:
        try:
            inspect = celery_app.control.inspect()
            stats = inspect.stats() if inspect else None
            workers_count = len(stats) if stats else 0
            return {
                "status": "healthy" if workers_count > 0 else "unhealthy",
                "workers_count": workers_count,
                "workers": list(stats.keys()) if stats else [],
            }
        except Exception as exc:
            return {"status": "unhealthy", "workers_count": 0, "error": str(exc)}

