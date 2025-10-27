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
        """Enhanced GraphiQL interface with quick login and examples"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>HumansOntology GraphQL Playground</title>
    <link rel="stylesheet" href="https://unpkg.com/graphiql@3.8.3/graphiql.min.css" />
    <style>
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        #toolbar {
            background: #1a202c;
            color: white;
            padding: 12px 20px;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        #toolbar h1 {
            margin: 0;
            font-size: 18px;
            font-weight: 600;
            flex-shrink: 0;
        }
        .btn-group {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .btn {
            padding: 6px 14px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .btn-primary {
            background: #3b82f6;
            color: white;
        }
        .btn-primary:hover { background: #2563eb; }
        .btn-success {
            background: #10b981;
            color: white;
        }
        .btn-success:hover { background: #059669; }
        .btn-warning {
            background: #f59e0b;
            color: white;
        }
        .btn-warning:hover { background: #d97706; }
        .btn-secondary {
            background: #6b7280;
            color: white;
        }
        .btn-secondary:hover { background: #4b5563; }
        .btn-danger {
            background: #ef4444;
            color: white;
        }
        .btn-danger:hover { background: #dc2626; }
        select {
            padding: 6px 12px;
            border: 1px solid #4b5563;
            border-radius: 6px;
            background: #374151;
            color: white;
            font-size: 13px;
            cursor: pointer;
        }
        #status {
            margin-left: auto;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
        }
        .status-authenticated {
            background: #dcfce7;
            color: #166534;
        }
        .status-anonymous {
            background: #fee2e2;
            color: #991b1b;
        }
        #graphiql { height: calc(100vh - 60px); }
    </style>
</head>
<body>
    <div id="toolbar">
        <h1>🧠 HumansOntology API</h1>

        <div class="btn-group">
            <button class="btn btn-success" onclick="quickLogin('admin')">👑 Admin</button>
            <button class="btn btn-primary" onclick="quickLogin('moderator')">👮 Moderator</button>
            <button class="btn btn-warning" onclick="quickLogin('editor')">✏️ Editor</button>
            <button class="btn btn-secondary" onclick="quickLogin('testuser')">👤 Testuser</button>
        </div>

        <select id="examples" onchange="loadExample()">
            <option value="">📝 Load Example...</option>
            <optgroup label="Authentication">
                <option value="auth.login">Login</option>
                <option value="auth.register">Register</option>
                <option value="auth.getCurrentUser">Get Current User</option>
                <option value="auth.refreshToken">Refresh Token</option>
            </optgroup>
            <optgroup label="Languages">
                <option value="languages.getAllLanguages">Get All Languages</option>
                <option value="languages.getLanguageById">Get Language by ID</option>
            </optgroup>
            <optgroup label="Concepts">
                <option value="concepts.getAllConcepts">Get All Concepts</option>
                <option value="concepts.getRootConcepts">Get Root Concepts</option>
                <option value="concepts.getConceptById">Get Concept by ID</option>
                <option value="concepts.createConcept">Create Concept</option>
            </optgroup>
            <optgroup label="Search">
                <option value="search.searchDictionaries">Search Dictionaries</option>
            </optgroup>
            <optgroup label="Admin">
                <option value="admin.getAllUsers">Get All Users</option>
                <option value="admin.getStatistics">Get Statistics</option>
                <option value="admin.updateUserStatus">Update User Status</option>
            </optgroup>
            <optgroup label="Audit">
                <option value="audit.getAuditLogs">Get Audit Logs</option>
                <option value="audit.getMyLogs">Get My Logs</option>
            </optgroup>
            <optgroup label="Profile">
                <option value="profile.updateProfile">Update Profile</option>
                <option value="profile.changePassword">Change Password</option>
            </optgroup>
        </select>

        <button class="btn btn-danger" onclick="logout()">🚪 Logout</button>

        <div id="status" class="status-anonymous">Anonymous</div>
    </div>

    <div id="graphiql"></div>

    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/graphiql@3.8.3/graphiql.min.js"></script>

    <script>
        let currentToken = localStorage.getItem('graphql_token') || '';
        let currentUser = JSON.parse(localStorage.getItem('graphql_user') || 'null');
        let examplesData = null;
        let graphiqlInstance = null;

        // Update status display
        function updateStatus() {
            const statusEl = document.getElementById('status');
            if (currentToken && currentUser) {
                statusEl.textContent = `✓ ${currentUser.username} (${currentUser.roles?.join(', ') || 'user'})`;
                statusEl.className = 'status-authenticated';
            } else {
                statusEl.textContent = 'Anonymous';
                statusEl.className = 'status-anonymous';
            }
        }

        // Quick login function
        async function quickLogin(username) {
            try {
                const response = await fetch(`/graphql/quick-login?user=${username}`);
                const data = await response.json();

                if (data.access_token) {
                    currentToken = data.access_token;
                    currentUser = data.user;
                    localStorage.setItem('graphql_token', currentToken);
                    localStorage.setItem('graphql_user', JSON.stringify(currentUser));
                    updateStatus();
                    alert(`✓ Logged in as ${username}\\n\\nToken copied to headers automatically!`);

                    // Reload GraphiQL with new token
                    initGraphiQL();
                } else {
                    alert('Login failed: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                alert('Login error: ' + error.message);
            }
        }

        // Logout function
        function logout() {
            currentToken = '';
            currentUser = null;
            localStorage.removeItem('graphql_token');
            localStorage.removeItem('graphql_user');
            updateStatus();
            alert('✓ Logged out');
            initGraphiQL();
        }

        // Load examples from API
        async function loadExamples() {
            try {
                const response = await fetch('/graphql/examples');
                examplesData = await response.json();
            } catch (error) {
                console.error('Failed to load examples:', error);
            }
        }

        // Load selected example
        function loadExample() {
            const select = document.getElementById('examples');
            const value = select.value;
            if (!value || !examplesData) return;

            const [category, name] = value.split('.');
            const example = examplesData[category]?.[name];

            if (example && graphiqlInstance) {
                // Update query editor
                graphiqlInstance.setState({
                    query: example.query
                });
                alert(`✓ Loaded: ${example.description}`);
            }

            select.value = '';
        }

        // Initialize GraphiQL
        function initGraphiQL() {
            const headers = currentToken
                ? { 'Authorization': `Bearer ${currentToken}` }
                : {};

            const fetcher = GraphiQL.createFetcher({
                url: '/graphql',
                headers: {
                    ...headers,
                    'Content-Type': 'application/json'
                }
            });

            const root = ReactDOM.createRoot(document.getElementById('graphiql'));
            root.render(
                React.createElement(GraphiQL, {
                    fetcher: fetcher,
                    defaultEditorToolsVisibility: true,
                    headers: JSON.stringify(headers, null, 2),
                    ref: (instance) => { graphiqlInstance = instance; }
                })
            );
        }

        // Initialize on load
        updateStatus();
        loadExamples();
        initGraphiQL();
    </script>
</body>
</html>
"""

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


# Quick login endpoint for GraphQL Playground
@app.route("/graphql/quick-login")
async def quick_login(request):
    """
    Quick login for GraphQL Playground - generates JWT tokens for seed users.
    Available users: admin, moderator, editor, testuser

    Usage: GET /graphql/quick-login?user=admin
    """
    from auth.models.user import User as UserModel
    from auth.utils.jwt_handler import jwt_handler
    from core.database import SessionLocal

    # Check if we're in development mode
    is_development = os.getenv("ENVIRONMENT", "development").lower() == "development"
    if not is_development:
        return JSONResponse(
            {"error": "Quick login is only available in development environment"},
            status_code=403
        )

    # Get username from query params (default: testuser)
    username = request.query_params.get("user", "testuser")

    # Map of available test users with their info
    available_users = {
        "admin": {"username": "admin", "description": "Full admin access"},
        "moderator": {"username": "moderator", "description": "User management"},
        "editor": {"username": "editor", "description": "Content management"},
        "testuser": {"username": "testuser", "description": "Regular user"}
    }

    if username not in available_users:
        return JSONResponse({
            "error": f"Unknown user '{username}'",
            "available_users": available_users
        }, status_code=400)

    db = SessionLocal()
    try:
        # Find the user from seed data
        user = db.query(UserModel).filter(UserModel.username == username).first()

        if not user:
            return JSONResponse({
                "error": f"User '{username}' not found. Make sure SEED_DATABASE=true",
                "available_users": list(available_users.keys())
            }, status_code=404)

        # Generate JWT tokens
        access_token = jwt_handler.generate_token(
            user.id,
            user.username,
            user.email,
            token_type="access"
        )

        refresh_token = jwt_handler.generate_token(
            user.id,
            user.username,
            user.email,
            token_type="refresh"
        )

        return JSONResponse({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "roles": [role.name for role in user.roles] if user.roles else []
            },
            "hint": f"Copy this to Headers: {{\"Authorization\": \"Bearer {access_token}\"}}"
        })
    except Exception as e:
        logger.error(f"Error generating token for {username}: {e}")
        return JSONResponse(
            {"error": f"Failed to generate token: {str(e)}"},
            status_code=500
        )
    finally:
        db.close()


# GraphQL examples endpoint for Playground
@app.route("/graphql/examples")
async def graphql_examples(request):
    """
    Real GraphQL query and mutation examples based on actual schema.
    Organized by category for easy navigation.
    """
    examples = {
        "auth": {
            "login": {
                "description": "Login with username and password",
                "query": """mutation Login {
  login(input: {username: "admin", password: "Admin123!"}) {
    accessToken
    refreshToken
    tokenType
  }
}"""
            },
            "register": {
                "description": "Register a new user account",
                "query": """mutation Register {
  register(input: {
    username: "newuser"
    email: "newuser@example.com"
    password: "SecurePass123!"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}"""
            },
            "getCurrentUser": {
                "description": "Get current authenticated user (requires auth)",
                "query": """query Me {
  me {
    id
    username
    email
    isActive
    isVerified
    profile {
      firstName
      lastName
      language
      timezone
    }
  }
}"""
            },
            "refreshToken": {
                "description": "Refresh access token",
                "query": """mutation RefreshToken {
  refreshToken(input: {refreshToken: "YOUR_REFRESH_TOKEN"}) {
    accessToken
    refreshToken
    tokenType
  }
}"""
            }
        },
        "languages": {
            "getAllLanguages": {
                "description": "Get all available languages",
                "query": """query GetLanguages {
  languages {
    id
    name
    code
    nativeName
    isActive
  }
}"""
            },
            "getLanguageById": {
                "description": "Get single language by ID",
                "query": """query GetLanguage {
  language(languageId: 1) {
    id
    name
    code
    nativeName
    isActive
  }
}"""
            }
        },
        "concepts": {
            "getAllConcepts": {
                "description": "Get all concepts",
                "query": """query GetConcepts {
  concepts {
    id
    path
    depth
    dictionaries {
      name
      description
      language {
        code
      }
    }
  }
}"""
            },
            "getRootConcepts": {
                "description": "Get only root concepts (depth=0)",
                "query": """query GetRootConcepts {
  concepts(depth: 0) {
    id
    path
    depth
  }
}"""
            },
            "getConceptById": {
                "description": "Get single concept with translations",
                "query": """query GetConcept {
  concept(conceptId: 1) {
    id
    path
    depth
    dictionaries {
      name
      description
      language {
        name
        code
      }
    }
  }
}"""
            },
            "createConcept": {
                "description": "Create a new concept (root level)",
                "query": """mutation CreateConcept {
  createConcept(input: {
    path: "animals"
    depth: 0
    parentId: null
  }) {
    id
    path
    depth
  }
}"""
            }
        },
        "search": {
            "searchDictionaries": {
                "description": "Full-text search across dictionaries",
                "query": """query Search {
  search(query: "science", languageCode: "en", limit: 10) {
    id
    name
    description
    concept {
      id
      path
    }
    language {
      name
      code
    }
  }
}"""
            }
        },
        "admin": {
            "getAllUsers": {
                "description": "Get all users (admin only)",
                "query": """query GetUsers {
  users(limit: 20, offset: 0) {
    id
    username
    email
    isActive
    isVerified
  }
}"""
            },
            "getStatistics": {
                "description": "Get system statistics (admin only)",
                "query": """query GetStats {
  statistics {
    totalUsers
    activeUsers
    totalLanguages
    totalConcepts
    totalDictionaries
  }
}"""
            },
            "updateUserStatus": {
                "description": "Activate/deactivate user (admin only)",
                "query": """mutation UpdateUserStatus {
  updateUserStatus(userId: 5, isActive: true) {
    id
    username
    isActive
  }
}"""
            }
        },
        "audit": {
            "getAuditLogs": {
                "description": "Get system audit logs (admin only)",
                "query": """query GetAuditLogs {
  auditLogs(limit: 50, filters: {action: "login"}) {
    logs {
      id
      userId
      action
      entityType
      status
      ipAddress
      createdAt
    }
    total
    hasMore
  }
}"""
            },
            "getMyLogs": {
                "description": "Get current user's audit logs",
                "query": """query GetMyAuditLogs {
  myAuditLogs(limit: 20) {
    logs {
      id
      action
      status
      createdAt
    }
    total
  }
}"""
            }
        },
        "profile": {
            "updateProfile": {
                "description": "Update current user profile",
                "query": """mutation UpdateProfile {
  updateProfile(
    firstName: "John"
    lastName: "Doe"
    bio: "Software Developer"
    language: "en"
    timezone: "UTC"
  ) {
    id
    profile {
      firstName
      lastName
      bio
    }
  }
}"""
            },
            "changePassword": {
                "description": "Change current user password",
                "query": """mutation ChangePassword {
  changePassword(
    currentPassword: "OldPassword123!"
    newPassword: "NewSecurePassword456!"
  ) {
    success
    message
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
