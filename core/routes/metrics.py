from starlette.responses import Response
from starlette.routing import Router

from core.metrics import get_metrics, update_db_pool_metrics


async def metrics_endpoint(request):
    """
    Точка сбора метрик Prometheus. Обновляет показатели пула БД перед отдачей.
    """
    update_db_pool_metrics()

    metrics_data, content_type = get_metrics()
    return Response(content=metrics_data, media_type=content_type)


def register_routes(app: Router) -> None:
    """Добавляет endpoint /metrics."""
    app.add_route("/metrics", metrics_endpoint, methods=["GET"])

