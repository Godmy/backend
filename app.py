import logging
import os
import time

import strawberry
import uvicorn
from sqlalchemy import text
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from strawberry.asgi import GraphQL

from auth.services.user_service import UserService
from auth.utils.jwt_handler import jwt_handler
from core.database import engine, get_db
from core.init_db import init_database
from core.schemas.schema import schema
from core.sentry import add_breadcrumb, init_sentry, set_user_context
from core.middleware import (
    PrometheusMiddleware,
    SecurityHeadersMiddleware,
    ShutdownMiddleware,
    RequestLoggingMiddleware
)
from core.shutdown import setup_graceful_shutdown

# Настройка логирования с request_id
from core.context import RequestContextFilter

logging.basicConfig(
    level=logging.INFO,
    format='[%(request_id)s] [user:%(user_id)s] %(levelname)s - %(name)s - %(message)s'
)

# Add context filter to root logger and all existing handlers
root_logger = logging.getLogger()
context_filter = RequestContextFilter()
root_logger.addFilter(context_filter)

# Also add filter to all existing handlers
for handler in root_logger.handlers:
    handler.addFilter(context_filter)

logger = logging.getLogger(__name__)

# Инициализация Sentry для error tracking и monitoring
init_sentry()

# Инициализация базы данных
# Проверяем переменную окружения SEED_DATABASE
seed_db = os.getenv("SEED_DATABASE", "true").lower() == "true"
init_database(seed=seed_db)


# Context getter function for GraphQL (ASYNC VERSION for Strawberry ASGI)
async def get_graphql_context(request=None, response=None):
    """
    Создание контекста для GraphQL запросов.

    NOTE: DB session is managed by DatabaseSessionExtension (in core.graphql_extensions)
    and will be automatically added to context before query execution.
    """
    from core.context import get_request_id

    # Get request ID from context (set by RequestLoggingMiddleware)
    request_id = get_request_id()

    context = {
        "request": request,
        "response": response,
        # "db" will be added by DatabaseSessionExtension
        "request_id": request_id,
    }

    # Пытаемся получить пользователя из токена
    # NOTE: We create a temporary DB session here just for authentication
    # The actual GraphQL queries will use the session from DatabaseSessionExtension
    if request:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            from core.database import SessionLocal

            token = auth_header.split("Bearer ")[1]
            auth_db = None
            try:
                payload = jwt_handler.verify_token(token)
                if payload and payload.get("type") == "access":
                    user_id = payload.get("user_id")
                    # Create temporary session for authentication only
                    auth_db = SessionLocal()
                    user = UserService.get_user_by_id(auth_db, user_id)
                    if user and user.is_active:
                        context["user"] = user
                        # Set Sentry user context for error tracking
                        set_user_context(
                            user_id=user.id, username=user.username, email=user.email
                        )
                        # Add breadcrumb for authenticated request
                        add_breadcrumb(
                            f"Authenticated request from user {user.username}",
                            category="auth",
                            level="info",
                        )
            except Exception as e:
                logger.debug(f"Token verification failed: {e}")
            finally:
                # Always close the temporary auth session
                if auth_db:
                    auth_db.close()

    return context


# Note: DB session cleanup is now handled by DatabaseSessionExtension (in core.graphql_extensions)
# which automatically closes sessions after each GraphQL request execution.

# Create custom GraphQL app class to inject context
class CustomGraphQL(GraphQL):
    async def get_context(self, request, response=None):
        """Override get_context to inject our custom context"""
        return await get_graphql_context(request, response)

graphql_app = CustomGraphQL(schema)

# Создаем Starlette приложение с CORS
app = Starlette()

# Add Shutdown middleware (first, to reject requests during shutdown)
app.add_middleware(ShutdownMiddleware)

# Add Request Logging middleware (before security headers for complete logging)
app.add_middleware(RequestLoggingMiddleware, log_body=True, log_headers=False)

# Add Security Headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware)

# Add CORS middleware with special handling for SSR
# Get allowed origins from environment variable
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]

logger.info(f"CORS allowed origins from env: {allowed_origins}")

# For SSR, allow all origins (since it's server-to-server communication)
# Using wildcard "*" for allow_origins to support SSR requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins to support SSR
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем GraphQL
app.mount("/graphql", graphql_app)


# Health check endpoints
@app.route("/health")
async def health_check(request):
    """Simple health check endpoint (backward compatible)"""
    from core.shutdown import shutdown_handler

    # Return 503 if shutting down
    if shutdown_handler.is_shutting_down():
        return JSONResponse(
            {"status": "unhealthy", "message": "Application is shutting down"},
            status_code=503
        )

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return JSONResponse({"status": "healthy", "database": "connected"})
    except Exception as e:
        return JSONResponse(
            {"status": "unhealthy", "database": "disconnected", "error": str(e)}, status_code=503
        )


@app.route("/health/detailed")
async def detailed_health_check(request):
    """Detailed health check endpoint with all system components"""
    from core.services.health_service import HealthCheckService
    from core.shutdown import shutdown_handler

    # Return 503 if shutting down
    if shutdown_handler.is_shutting_down():
        return JSONResponse(
            {
                "status": "unhealthy",
                "message": "Application is shutting down",
                "timestamp": time.time()
            },
            status_code=503
        )

    health_status = HealthCheckService.get_full_health_status()

    # Set appropriate HTTP status code
    status_code = 200
    if health_status["status"] == "unhealthy":
        status_code = 503
    elif health_status["status"] == "degraded":
        status_code = 200  # Still operational but with warnings

    return JSONResponse(health_status, status_code=status_code)


@app.route("/metrics")
async def metrics_endpoint(request):
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus exposition format for scraping.
    Includes HTTP, GraphQL, database, Redis, business logic, and system metrics.
    Also updates database connection pool metrics on each scrape.
    """
    from starlette.responses import Response
    from core.metrics import get_metrics, update_db_pool_metrics

    # Update DB pool metrics before returning
    update_db_pool_metrics()

    metrics_data, content_type = get_metrics()
    return Response(content=metrics_data, media_type=content_type)


# Для корневого пути можно сделать редирект
@app.route("/")
async def homepage(request):
    from starlette.responses import RedirectResponse

    return RedirectResponse(url="/graphql")


# Endpoint для получения загруженных файлов
@app.route("/uploads/{filename:path}")
async def serve_file(request):
    import os
    from pathlib import Path

    from starlette.responses import FileResponse

    filename = request.path_params["filename"]
    upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads"))

    # Проверка на path traversal атаки
    file_path = (upload_dir / filename).resolve()
    if not str(file_path).startswith(str(upload_dir.resolve())):
        return JSONResponse({"error": "Invalid file path"}, status_code=400)

    if not file_path.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)

    return FileResponse(file_path)


# Endpoint для получения экспортированных файлов
@app.route("/exports/{filename:path}")
async def serve_export(request):
    import os
    from pathlib import Path

    from starlette.responses import FileResponse

    filename = request.path_params["filename"]
    export_dir = Path(os.getenv("EXPORT_DIR", "exports"))

    # Проверка на path traversal атаки
    file_path = (export_dir / filename).resolve()
    if not str(file_path).startswith(str(export_dir.resolve())):
        return JSONResponse({"error": "Invalid file path"}, status_code=400)

    if not file_path.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)

    return FileResponse(file_path)


if __name__ == "__main__":
    # Setup graceful shutdown handlers
    shutdown_timeout = int(os.getenv("SHUTDOWN_TIMEOUT", "30"))
    setup_graceful_shutdown(shutdown_timeout=shutdown_timeout)
    logger.info(f"Graceful shutdown configured with {shutdown_timeout}s timeout")

    # Run application with graceful shutdown support
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        timeout_graceful_shutdown=shutdown_timeout
    )
