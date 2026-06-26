from __future__ import annotations

import os

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from auth.utils.jwt_handler import jwt_handler
from core.platform.db.init_db import init_database
from core.platform.logging.structured_logging import setup_logging


class StarletteConfig:
    def setup_logging(self) -> None:
        setup_logging()

    def initialize_sentry(self) -> None:
        return None

    def initialize_database(self) -> None:
        init_database(stage="app")

    def create_app(self, graphql_app, logger=None) -> Starlette:
        from core.domains.health import HealthCheckService

        async def health_live(_request):
            """Liveness: приложение запущено."""
            return JSONResponse({"status": "ok"})

        async def health_ready(_request):
            """Readiness: обязательные зависимости (DB + Redis) доступны."""
            result = HealthCheckService.readiness_check()
            code = 200 if result["status"] == "healthy" else 503
            return JSONResponse(result, status_code=code)

        async def health(_request):
            """Full health: все сервисы с латентностью и статусом."""
            result = HealthCheckService.full_check()
            codes = {"healthy": 200, "degraded": 207, "unhealthy": 503}
            return JSONResponse(result, status_code=codes.get(result["status"], 503))

        async def graphql_examples(_request):
            return JSONResponse(
                {
                    "queries": {
                        "health": "query { __typename }",
                    },
                    "mutations": {
                        "login": (
                            'mutation { login(input: { username: "admin", password: "admin" }) '
                            "{ accessToken refreshToken tokenType } }"
                        ),
                    },
                }
            )

        async def test_user_login(_request):
            if os.getenv("ENVIRONMENT", "development") != "development":
                return JSONResponse(
                    {"error": "Endpoint is available only in development"},
                    status_code=403,
                )

            token_data = {
                "sub": "test_user",
                "user_id": 1,
                "email": "test_user@example.com",
            }
            return JSONResponse(
                {
                    "access_token": jwt_handler.create_access_token(token_data),
                    "refresh_token": jwt_handler.create_refresh_token(token_data),
                    "token_type": "bearer",
                    "user": {
                        "id": 1,
                        "username": "test_user",
                        "email": "test_user@example.com",
                    },
                }
            )

        routes = [
            Route("/health", health),
            Route("/health/live", health_live),
            Route("/health/ready", health_ready),
            Route("/graphql/examples", graphql_examples),
            Route("/graphql/test-user-login", test_user_login),
            Mount("/graphql", graphql_app),
        ]

        app = Starlette(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            routes=routes,
            on_startup=[self.initialize_database],
        )
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                origin.strip()
                for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
                if origin.strip()
            ],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )
        return app
