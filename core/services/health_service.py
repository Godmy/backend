"""
Health check service for monitoring system components.

Provides detailed health checks for:
- Database connectivity and performance
- Redis connectivity and performance
- Disk space availability
- Memory usage
"""

import logging
import os
import time
from typing import Dict, Any

import psutil
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.database import engine

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Service for checking health of system components"""

    @staticmethod
    def check_database() -> Dict[str, Any]:
        """
        Check database connectivity and performance.

        Returns:
            Dict with status, connection time, and error if any
        """
        try:
            start_time = time.time()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            end_time = time.time()
            response_time_ms = round((end_time - start_time) * 1000, 2)

            return {
                "status": "healthy",
                "response_time_ms": response_time_ms,
                "message": "Database connection successful",
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e), "message": "Database connection failed"}

    @staticmethod
    def check_redis() -> Dict[str, Any]:
        """
        Check Redis connectivity and performance.

        Returns:
            Dict with status, connection time, and error if any
        """
        try:
            from core.redis_client import redis_client

            start_time = time.time()
            redis_client.ping()
            end_time = time.time()
            response_time_ms = round((end_time - start_time) * 1000, 2)

            return {
                "status": "healthy",
                "response_time_ms": response_time_ms,
                "message": "Redis connection successful",
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {"status": "unhealthy", "error": str(e), "message": "Redis connection failed"}

    @staticmethod
    def check_disk_space(threshold_percent: int = 90) -> Dict[str, Any]:
        """
        Check disk space availability.

        Args:
            threshold_percent: Warning threshold for disk usage (default: 90%)

        Returns:
            Dict with status, disk usage info, and warning if threshold exceeded
        """
        try:
            disk = psutil.disk_usage("/")
            percent_used = disk.percent

            status = "healthy"
            message = f"Disk usage at {percent_used}%"

            if percent_used >= threshold_percent:
                status = "warning"
                message = f"Disk usage is high: {percent_used}% (threshold: {threshold_percent}%)"

            return {
                "status": status,
                "percent_used": percent_used,
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "message": message,
            }
        except Exception as e:
            logger.error(f"Disk space health check failed: {e}")
            return {"status": "unhealthy", "error": str(e), "message": "Disk check failed"}

    @staticmethod
    def check_memory(threshold_percent: int = 90) -> Dict[str, Any]:
        """
        Check memory usage.

        Args:
            threshold_percent: Warning threshold for memory usage (default: 90%)

        Returns:
            Dict with status, memory usage info, and warning if threshold exceeded
        """
        try:
            memory = psutil.virtual_memory()
            percent_used = memory.percent

            status = "healthy"
            message = f"Memory usage at {percent_used}%"

            if percent_used >= threshold_percent:
                status = "warning"
                message = (
                    f"Memory usage is high: {percent_used}% (threshold: {threshold_percent}%)"
                )

            return {
                "status": status,
                "percent_used": percent_used,
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "message": message,
            }
        except Exception as e:
            logger.error(f"Memory health check failed: {e}")
            return {"status": "unhealthy", "error": str(e), "message": "Memory check failed"}

    @staticmethod
    async def check_cache() -> Dict[str, Any]:
        """
        Check cache health status.

        Returns:
            Dict with cache health information including key count and usage
        """
        try:
            from core.services.cache_service import get_cache_health

            cache_health = await get_cache_health()
            return cache_health
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "error",
                "available": False,
                "error": str(e),
                "message": "Cache health check failed"
            }

    @classmethod
    async def get_full_health_status(cls) -> Dict[str, Any]:
        """
        Get comprehensive health status of all system components.

        Returns:
            Dict with overall status and individual component statuses
        """
        database = cls.check_database()
        redis = cls.check_redis()
        disk = cls.check_disk_space()
        memory = cls.check_memory()
        cache = await cls.check_cache()

        # Determine overall status
        components = [database, redis, disk, memory, cache]
        if any(c["status"] == "unhealthy" for c in components):
            overall_status = "unhealthy"
        elif any(c["status"] in ["warning", "degraded", "critical"] for c in components):
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "components": {
                "database": database,
                "redis": redis,
                "disk": disk,
                "memory": memory,
                "cache": cache
            },
        }
