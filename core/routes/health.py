import time

from sqlalchemy import text
from starlette.responses import JSONResponse
from starlette.routing import Router

from core.database import engine
from core.services.health_service import HealthCheckService
from core.shutdown import shutdown_handler


async def health_check(request):
    """Простой healthcheck для обратной совместимости."""
    if shutdown_handler.is_shutting_down():
        return JSONResponse(
            {"status": "unhealthy", "message": "Application is shutting down"},
            status_code=503,
        )

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return JSONResponse({"status": "healthy", "database": "connected"})
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(exc),
            },
            status_code=503,
        )


async def detailed_health_check(request):
    """Расширенный healthcheck со всеми компонентами системы."""
    if shutdown_handler.is_shutting_down():
        return JSONResponse(
            {
                "status": "unhealthy",
                "message": "Application is shutting down",
                "timestamp": time.time(),
            },
            status_code=503,
        )

    health_status = await HealthCheckService.get_full_health_status()

    status_code = 200
    if health_status["status"] == "unhealthy":
        status_code = 503

    return JSONResponse(health_status, status_code=status_code)


def register_routes(app: Router) -> None:
    """Добавляет health-эндпоинты в приложение."""
    app.add_route("/health", health_check, methods=["GET"])
    app.add_route("/health/detailed", detailed_health_check, methods=["GET"])

