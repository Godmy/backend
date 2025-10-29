import os
from logging import Logger
from typing import Optional

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware

from core.init_db import init_database
from core.middleware import (
    CacheControlMiddleware,
    PrometheusMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    ShutdownMiddleware,
)
from core.sentry import init_sentry
from core.structured_logging import setup_logging
from core.routes import register_routes as register_http_routes


class StarletteConfig:
    """
    Инкапсулирует настройку инфраструктурных зависимостей и конфигурацию Starlette.
    Позволяет централизованно управлять порядком инициализации и избежать побочных
    эффектов при импорте модуля приложения.
    """

    def __init__(self) -> None:
        self.environment = os.getenv("ENVIRONMENT", "development").lower()
        self.allowed_origins_env = os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:5173"
        )
        self.seed_database = os.getenv("SEED_DATABASE", "true").lower() == "true"
        self._allowed_origins = [
            origin.strip() for origin in self.allowed_origins_env.split(",")
        ]

    def setup_logging(self) -> None:
        """Настраивает структурированное логирование."""
        setup_logging()

    def initialize_sentry(self) -> None:
        """Запускает интеграцию с Sentry."""
        init_sentry()

    def initialize_database(self) -> None:
        """Инициализирует базу данных (включая сидирование при необходимости)."""
        init_database(seed=self.seed_database)

    def create_app(
        self, graphql_app: object, logger: Optional[Logger] = None
    ) -> Starlette:
        """
        Создаёт и настраивает экземпляр Starlette, монтирует GraphQL-приложение
        и возвращает готовый объект `app`.
        """
        app = Starlette()
        self._configure_middlewares(app)
        self._configure_cors(app, logger=logger)
        app.mount("/graphql", graphql_app)
        register_http_routes(app)
        return app

    def _configure_middlewares(self, app: Starlette) -> None:
        """Добавляет middleware в порядке приоритета."""
        app.add_middleware(ShutdownMiddleware)
        app.add_middleware(RateLimitMiddleware)
        app.add_middleware(CacheControlMiddleware)
        app.add_middleware(RequestLoggingMiddleware, log_body=True, log_headers=False)
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(PrometheusMiddleware)

    def _configure_cors(self, app: Starlette, logger: Optional[Logger] = None) -> None:
        """Настраивает CORS в зависимости от окружения."""
        if logger:
            logger.info(f"CORS allowed origins from env: {self._allowed_origins}")

        if self.environment == "development":
            allow_origins = ["*"]
            allow_credentials = False
        else:
            allow_origins = self._allowed_origins
            allow_credentials = True

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=allow_credentials,
            allow_methods=["*"],
            allow_headers=["*"],
        )
