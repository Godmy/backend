from __future__ import annotations

from strawberry.asgi import GraphQL

from core.platform.config import get_settings


GRAPHQL_PLAYGROUND_ENABLED = get_settings().graphql_playground_enabled


class SecureGraphQL(GraphQL):
    async def get_context(self, request, response):
        return {
            "request": request,
            "response": response,
        }

    def __init__(self, schema, **kwargs):
        super().__init__(schema=schema, **kwargs)


__all__ = ["GRAPHQL_PLAYGROUND_ENABLED", "SecureGraphQL"]
