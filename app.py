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
    RequestLoggingMiddleware,
    RateLimitMiddleware,
    CacheControlMiddleware
)
from core.shutdown import setup_graceful_shutdown

# Setup structured logging (JSON format)
from core.structured_logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

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

from starlette.responses import HTMLResponse, JSONResponse
from starlette.requests import Request

# Create custom GraphQL app class to inject context
class CustomGraphQL(GraphQL):
    async def get_context(self, request, response=None):
        """Override get_context to inject our custom context"""
        return await get_graphql_context(request, response)

# Create GraphQL app with environment-based configuration
GRAPHQL_PLAYGROUND_ENABLED = os.getenv("GRAPHQL_PLAYGROUND_ENABLED", "true").lower() == "true"
GRAPHQL_PLAYGROUND_AUTH_REQUIRED = os.getenv("GRAPHQL_PLAYGROUND_AUTH_REQUIRED", "false").lower() == "true"

class SecureGraphQL(GraphQL):
    """
    A custom GraphQL app that provides additional security for the Playground
    and allows conditional authentication
    """
    
    def __init__(self, schema, **kwargs):
        super().__init__(schema, **kwargs)
    
    async def __call__(self, scope, receive, send):
        from core.structured_logging import get_logger
        logger = get_logger(__name__)
        
        request = Request(scope)
        
        # Check if this is a request for the GraphiQL interface
        if scope['type'] == 'http' and scope['method'] == 'GET':
            if GRAPHQL_PLAYGROUND_AUTH_REQUIRED:
                # Check for authorization header
                auth_header = request.headers.get('Authorization')
                
                # For development purposes, we can bypass auth with a special header
                if not auth_header and not (os.getenv("ENVIRONMENT", "development").lower() == "development"):
                    # In production or when auth is required, return error
                    response = JSONResponse(
                        status_code=401,
                        content={"error": "Authentication required for GraphQL Playground"}
                    )
                    await response(scope, receive, send)
                    return
                
                # Validate if we have a proper Bearer token
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    try:
                        from auth.utils.jwt_handler import jwt_handler
                        payload = jwt_handler.verify_token(token)
                        
                        # If token is invalid, allow to access but show warning in playground
                        # Or validate against your user system if needed
                    except Exception as e:
                        # Token is invalid, but we'll still allow access to playground
                        # for debugging purposes, just log this
                        logger.warning(f"Invalid token provided for GraphQL Playground: {e}")
        
        # Check if this request is coming from GraphQL Playground
        is_playground_request = (
            request.headers.get('X-GraphQL-Client') == 'Playground' or
            request.headers.get('X-GraphQL-Request-Source') == 'Playground' or
            'graphiql' in request.headers.get('user-agent', '').lower()
        )
        
        # Log the request if it's from Playground
        if is_playground_request:
            logger.info(
                "GraphQL Playground request",
                extra={
                    "event": "graphql_playground_request",
                    "path": request.url.path,
                    "method": request.method,
                    "headers": dict(request.headers),
                    "user_agent": request.headers.get('user-agent'),
                }
            )
        
        # Call the original ASGI app
        await super().__call__(scope, receive, send)

    def get_graphiql_html(self, **kwargs) -> str:
        """Override to customize the GraphiQL interface with default headers"""
        # Get default headers from environment variables
        default_headers_str = os.getenv("GRAPHQL_PLAYGROUND_DEFAULT_HEADERS", "{}")
        try:
            import json
            default_headers = json.loads(default_headers_str)
        except json.JSONDecodeError:
            default_headers = {"Content-Type": "application/json"}
        
        # Add JavaScript to set default headers in the GraphiQL interface
        graphiql_with_default_headers = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>GraphQL Playground</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/graphiql@2/graphiql.min.css" />
        </head>
        <body style="margin: 0;">
            <div id="graphiql" style="height: 100vh;"></div>
            
            <script src="https://cdn.jsdelivr.net/npm/react@18/umd/react.production.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/react-dom@18/umd/react-dom.production.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/graphiql@2/graphiql.min.js"></script>
            
            <script>
                // Default headers from environment
                const defaultHeaders = {default_headers_str or '{{"Content-Type": "application/json"}}'};
                
                // Enhance fetcher to add custom headers and tracking
                const fetcher = GraphiQL.createFetcher({{
                    url: '{kwargs.get('endpoint', '/graphql')}',
                    subscriptionUrl: '{kwargs.get('subscription_endpoint', '')}',
                    headers: {{
                        ...defaultHeaders,
                        'X-GraphQL-Client': 'Playground',
                        'X-GraphQL-Request-Source': 'Playground'
                    }}
                }});
                
                ReactDOM.render(
                    React.createElement(GraphiQL, {{
                        fetcher: fetcher,
                        defaultEditorToolsVisibility: true,
                        headers: defaultHeaders
                    }}),
                    document.getElementById('graphiql')
                );
            </script>
        </body>
        </html>
        """
        return graphiql_with_default_headers

async def process_graphql_operation(self, request, *args, **kwargs):
    """
    Override to add logging for GraphQL Playground requests
    """
    # Check if this request is coming from GraphQL Playground
    is_playground_request = (
        request.headers.get('X-GraphQL-Client') == 'Playground' or
        request.headers.get('X-GraphQL-Request-Source') == 'Playground' or
        'graphiql' in request.headers.get('user-agent', '').lower()
    )
    
    from core.structured_logging import get_logger
    logger = get_logger(__name__)
    
    # Log the request if it's from Playground
    if is_playground_request:
        logger.info(
            "GraphQL Playground request",
            extra={
                "event": "graphql_playground_request",
                "path": request.url.path,
                "method": request.method,
                "headers": dict(request.headers),
                "user_agent": request.headers.get('user-agent'),
            }
        )
    
    # Process the original request
    return await super(SecureGraphQL, self).__call__(request.scope, request.receive, request.send)


# Use the secure GraphQL implementation
graphql_app = SecureGraphQL(
    schema,
    graphiql=GRAPHQL_PLAYGROUND_ENABLED,  # Enable/disable GraphQL Playground (GraphiQL)
)

# Создаем Starlette приложение с CORS
app = Starlette()

# Add Shutdown middleware (first, to reject requests during shutdown)
app.add_middleware(ShutdownMiddleware)

# Add Rate Limiting middleware (early, to block excessive requests before processing)
app.add_middleware(RateLimitMiddleware)

# Add Cache Control middleware (add caching headers and handle 304 responses)
app.add_middleware(CacheControlMiddleware)

# Add Request Logging middleware (logs all requests including rate-limited ones)
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

# Configure CORS based on environment - more restrictive for production
is_development = os.getenv("ENVIRONMENT", "development").lower() == "development"
if is_development:
    cors_allow_origins = ["*"]  # Allow all origins in development
    cors_allow_credentials = False
else:
    # In production, only allow specified origins
    cors_allow_origins = allowed_origins
    cors_allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_credentials=cors_allow_credentials,
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

    health_status = await HealthCheckService.get_full_health_status()

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


# Test user login endpoint for GraphQL Playground
@app.route("/graphql/test-user-login")
async def test_user_login(request):
    """
    Generate a test user JWT token for use in GraphQL Playground.
    This provides an easy way to test authenticated GraphQL queries.
    """
    from auth.models.user import User
    from auth.utils.jwt_handler import jwt_handler
    from core.database import SessionLocal
    
    # Check if we're in development mode
    is_development = os.getenv("ENVIRONMENT", "development").lower() == "development"
    if not is_development:
        return JSONResponse(
            {"error": "Test user login is only available in development environment"},
            status_code=403
        )
    
    # Create or get a test user
    db = SessionLocal()
    try:
        # Try to find an existing test user
        test_user = db.query(User).filter(User.username == "test_user").first()
        
        if not test_user:
            # Create a test user if one doesn't exist
            from auth.services.user_service import UserService
            from auth.models.user import User
            from core.database import hash_password
            import uuid

            test_user = User(
                id=str(uuid.uuid4()),
                username="test_user",
                email="test@example.com",
                password=hash_password("test_password"),  # Use default test password
                is_active=True,
                is_verified=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        
        # Generate JWT token for the test user
        access_token = jwt_handler.generate_token(
            test_user.id,
            test_user.username,
            test_user.email,
            token_type="access"
        )
        
        refresh_token = jwt_handler.generate_token(
            test_user.id, 
            test_user.username,
            test_user.email,
            token_type="refresh"
        )
        
        return JSONResponse({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": test_user.id,
                "username": test_user.username,
                "email": test_user.email
            }
        })
    except Exception as e:
        logger.error(f"Error creating/generating test user token: {e}")
        return JSONResponse(
            {"error": "Failed to generate test user token"},
            status_code=500
        )
    finally:
        db.close()


# GraphQL query examples endpoint for GraphQL Playground
@app.route("/graphql/examples")
async def graphql_examples(request):
    """
    Provides common GraphQL query and mutation examples for use in GraphQL Playground.
    """
    examples = {
        "queries": {
            "getAllLanguages": {
                "description": "Get all available languages",
                "query": """query GetAllLanguages {
  languages {
    id
    name
    code
    is_active
  }
}"""
            },
            "getConceptsByLanguage": {
                "description": "Get concepts for a specific language",
                "query": """query GetConceptsByLanguage($languageId: ID!) {
  concepts(languageId: $languageId) {
    id
    name
    description
    translations {
      language {
        code
      }
      value
    }
  }
}"""
            },
            "searchConcepts": {
                "description": "Search concepts by name or description",
                "query": """query SearchConcepts($searchTerm: String!) {
  searchConcepts(query: $searchTerm) {
    id
    name
    description
    language {
      name
    }
  }
}"""
            }
        },
        "mutations": {
            "createLanguage": {
                "description": "Create a new language",
                "query": """mutation CreateLanguage($name: String!, $code: String!) {
  createLanguage(input: {name: $name, code: $code}) {
    id
    name
    code
    is_active
  }
}"""
            },
            "createConcept": {
                "description": "Create a new concept",
                "query": """mutation CreateConcept($name: String!, $description: String!, $languageId: ID!) {
  createConcept(input: {name: $name, description: $description, languageId: $languageId}) {
    id
    name
    description
    language {
      id
      name
    }
  }
}"""
            }
        }
    }
    return JSONResponse(examples)


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
