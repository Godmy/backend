from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    database_url: str
    debug: bool
    environment: str
    app_host: str
    app_port: int
    allowed_origins: list[str]
    graphql_playground_enabled: bool
    whisper_gateway_url: str


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "postgres")
        database_url = (
            f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )

    environment = os.getenv("ENVIRONMENT", "development")
    debug = _to_bool(os.getenv("DEBUG"), environment != "production")
    playground_enabled = _to_bool(
        os.getenv("GRAPHQL_PLAYGROUND_ENABLED"),
        environment != "production",
    )
    allowed_origins = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]

    return Settings(
        database_url=database_url,
        debug=debug,
        environment=environment,
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        allowed_origins=allowed_origins,
        graphql_playground_enabled=playground_enabled,
        whisper_gateway_url=os.getenv("WHISPER_GATEWAY_URL", "http://gateway-whisper:8010"),
    )

