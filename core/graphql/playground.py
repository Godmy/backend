import os
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse
from strawberry.asgi import GraphQL

from auth.utils.jwt_handler import jwt_handler
from core.structured_logging import get_logger

from .graphql_context import get_graphql_context

GRAPHQL_PLAYGROUND_ENABLED = os.getenv("GRAPHQL_PLAYGROUND_ENABLED", "true").lower() == "true"
GRAPHQL_PLAYGROUND_AUTH_REQUIRED = os.getenv("GRAPHQL_PLAYGROUND_AUTH_REQUIRED", "false").lower() == "true"

logger = get_logger(__name__)

GRAPHIQL_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>HumansOntology GraphQL Playground</title>
    <link rel="stylesheet" href="https://unpkg.com/graphiql@3.8.3/graphiql.min.css" />
    <style>
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
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
        .btn-primary { background: #3b82f6; color: white; }
        .btn-primary:hover { background: #2563eb; }
        .btn-success { background: #10b981; color: white; }
        .btn-success:hover { background: #059669; }
        .btn-warning { background: #f59e0b; color: white; }
        .btn-warning:hover { background: #d97706; }
        .btn-secondary { background: #6b7280; color: white; }
        .btn-secondary:hover { background: #4b5563; }
        .btn-danger { background: #ef4444; color: white; }
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
        .status-authenticated { background: #dcfce7; color: #166534; }
        .status-anonymous { background: #fee2e2; color: #991b1b; }
        #graphiql { height: calc(100vh - 60px); }
    </style>
</head>
<body>
    <div id="toolbar">
        <h1>HumansOntology API</h1>

        <div class="btn-group">
            <button class="btn btn-success" onclick="quickLogin('admin')">Login as Admin</button>
            <button class="btn btn-primary" onclick="quickLogin('moderator')">Login as Moderator</button>
            <button class="btn btn-warning" onclick="quickLogin('editor')">Login as Editor</button>
            <button class="btn btn-secondary" onclick="quickLogin('testuser')">Login as Testuser</button>
        </div>

        <select id="examples" onchange="loadExample()">
            <option value="">Load Example…</option>
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

        <button class="btn btn-danger" onclick="logout()">Logout</button>

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

        function updateStatus() {
            const statusEl = document.getElementById('status');
            if (currentToken && currentUser) {
                statusEl.textContent = `Signed in as ${currentUser.username} (${currentUser.roles?.join(', ') || 'user'})`;
                statusEl.className = 'status-authenticated';
            } else {
                statusEl.textContent = 'Anonymous';
                statusEl.className = 'status-anonymous';
            }
        }

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
                    alert(`Logged in as ${username}. Token copied to headers automatically.`);
                    initGraphiQL();
                } else {
                    alert('Login failed: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                alert('Login error: ' + error.message);
            }
        }

        function logout() {
            currentToken = '';
            currentUser = null;
            localStorage.removeItem('graphql_token');
            localStorage.removeItem('graphql_user');
            updateStatus();
            alert('Logged out');
            initGraphiQL();
        }

        async function loadExamples() {
            try {
                const response = await fetch('/graphql/examples');
                examplesData = await response.json();
            } catch (error) {
                console.error('Failed to load examples:', error);
            }
        }

        function loadExample() {
            const select = document.getElementById('examples');
            const value = select.value;
            if (!value || !examplesData) return;

            const [category, name] = value.split('.');
            const example = examplesData[category]?.[name];

            if (example && graphiqlInstance) {
                graphiqlInstance.setState({
                    query: example.query
                });
                alert(`Loaded example: ${example.description}`);
            }

            select.value = '';
        }

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

        updateStatus();
        loadExamples();
        initGraphiQL();
    </script>
</body>
</html>
"""


def _is_playground_request(request: Request) -> bool:
    user_agent = request.headers.get("user-agent", "")
    return (
        request.headers.get("X-GraphQL-Client") == "Playground"
        or request.headers.get("X-GraphQL-Request-Source") == "Playground"
        or "graphiql" in user_agent.lower()
    )


class SecureGraphQL(GraphQL):
    """Custom GraphQL ASGI app with additional security checks for the Playground."""

    async def get_context(self, request: Any, response: Any = None) -> dict:
        return await get_graphql_context(request, response)

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        request = Request(scope)

        if scope.get("type") == "http" and scope.get("method") == "GET":
            if GRAPHQL_PLAYGROUND_AUTH_REQUIRED:
                auth_header = request.headers.get("Authorization")
                is_development = os.getenv("ENVIRONMENT", "development").lower() == "development"

                if not auth_header and not is_development:
                    response = JSONResponse(
                        status_code=401,
                        content={"error": "Authentication required for GraphQL Playground"},
                    )
                    await response(scope, receive, send)
                    return

                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    try:
                        jwt_handler.verify_token(token)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Invalid token provided for GraphQL Playground: %s", exc)

        if _is_playground_request(request):
            logger.info(
                "GraphQL Playground request",
                extra={
                    "event": "graphql_playground_request",
                    "path": request.url.path,
                    "method": request.method,
                    "headers": dict(request.headers),
                    "user_agent": request.headers.get("user-agent"),
                },
            )

        await super().__call__(scope, receive, send)

    async def process_graphql_operation(self, request: Request, *args: Any, **kwargs: Any):
        if _is_playground_request(request):
            logger.info(
                "GraphQL Playground request",
                extra={
                    "event": "graphql_playground_request",
                    "path": request.url.path,
                    "method": request.method,
                    "headers": dict(request.headers),
                    "user_agent": request.headers.get("user-agent"),
                },
            )

        return await super().process_graphql_operation(request, *args, **kwargs)

    def get_graphiql_html(self, **kwargs: Any) -> str:  # noqa: ARG002
        return GRAPHIQL_HTML


__all__ = [
    "GRAPHIQL_HTML",
    "GRAPHQL_PLAYGROUND_AUTH_REQUIRED",
    "GRAPHQL_PLAYGROUND_ENABLED",
    "SecureGraphQL",
]
