from __future__ import annotations

from typing import Any, Dict, Optional

from auth.services.user_service import UserService
from auth.utils.jwt_handler import jwt_handler
from core.sentry import add_breadcrumb, set_user_context
from core.structured_logging import get_logger

logger = get_logger(__name__)


async def get_graphql_context(
    request: Optional[Any] = None, response: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Build GraphQL context and enrich it with authentication information when available.

    DatabaseSessionExtension (core.graphql_extensions) injects the primary DB session
    before resolvers are executed.
    """
    from core.context import get_request_id

    request_id = get_request_id()

    context: Dict[str, Any] = {
        "request": request,
        "response": response,
        "request_id": request_id,
    }

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
                    auth_db = SessionLocal()
                    user = UserService.get_user_by_id(auth_db, user_id)
                    if user and user.is_active:
                        context["user"] = user
                        set_user_context(
                            user_id=user.id, username=user.username, email=user.email
                        )
                        add_breadcrumb(
                            f"Authenticated request from user {user.username}",
                            category="auth",
                            level="info",
                        )
            except Exception as exc:
                logger.debug("Token verification failed: %s", exc)
            finally:
                if auth_db:
                    auth_db.close()

    return context
