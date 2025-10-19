import logging
import os

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

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация Sentry для error tracking и monitoring
init_sentry()

# Инициализация базы данных
# Проверяем переменную окружения SEED_DATABASE
seed_db = os.getenv("SEED_DATABASE", "true").lower() == "true"
init_database(seed=seed_db)


# Создаем GraphQL app
class GraphQLWithContext(GraphQL):
    """GraphQL app с кастомным контекстом"""

    async def get_context(self, request, response=None):
        """Создание контекста для GraphQL запросов"""
        db = next(get_db())
        context = {"request": request, "response": response, "db": db}

        # Пытаемся получить пользователя из токена
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]
            try:
                payload = jwt_handler.verify_token(token)
                if payload and payload.get("type") == "access":
                    user_id = payload.get("user_id")
                    user = UserService.get_user_by_id(db, user_id)
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

        return context


graphql_app = GraphQLWithContext(schema)

# Создаем Starlette приложение с CORS
app = Starlette()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://frontend:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем GraphQL
app.mount("/graphql", graphql_app)


# Health check endpoints
@app.route("/health")
async def health_check(request):
    """Simple health check endpoint (backward compatible)"""
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

    health_status = HealthCheckService.get_full_health_status()

    # Set appropriate HTTP status code
    status_code = 200
    if health_status["status"] == "unhealthy":
        status_code = 503
    elif health_status["status"] == "degraded":
        status_code = 200  # Still operational but with warnings

    return JSONResponse(health_status, status_code=status_code)


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


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
