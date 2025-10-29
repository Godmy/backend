"""Регистрация HTTP-маршрутов Starlette."""

from starlette.routing import Router

from . import health, metrics, playground_utils, root, static_files


def register_routes(app: Router) -> None:
    """Подключает все маршруты приложения к экземпляру Starlette."""
    health.register_routes(app)
    metrics.register_routes(app)
    static_files.register_routes(app)
    playground_utils.register_routes(app)
    root.register_routes(app)


__all__ = ["register_routes"]

