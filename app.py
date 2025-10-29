import os

import uvicorn

from core.graphql import GRAPHQL_PLAYGROUND_ENABLED, SecureGraphQL
from core.schemas.schema import schema
from core.shutdown import setup_graceful_shutdown
from core.starlette_config import StarletteConfig
from core.structured_logging import get_logger

starlette_config = StarletteConfig()
starlette_config.setup_logging()
logger = get_logger(__name__)
starlette_config.initialize_sentry()
starlette_config.initialize_database()

# Note: DB session cleanup is handled by DatabaseSessionExtension (core.graphql_extensions).
graphql_app = SecureGraphQL(
    schema,
    graphiql=GRAPHQL_PLAYGROUND_ENABLED,
)

app = starlette_config.create_app(graphql_app, logger=logger)


if __name__ == "__main__":
    shutdown_timeout = int(os.getenv("SHUTDOWN_TIMEOUT", "30"))
    setup_graceful_shutdown(shutdown_timeout=shutdown_timeout)
    logger.info("Graceful shutdown configured with %ss timeout", shutdown_timeout)

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        timeout_graceful_shutdown=shutdown_timeout,
    )

