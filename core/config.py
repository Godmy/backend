"""
Environment Configuration Validator

This module provides centralized configuration management with validation.
All environment variables are validated on application startup using Pydantic.

Task: #37 - Environment Configuration Validator (BACKLOG.md)
"""

import os
import re
from pathlib import Path
from typing import Optional

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with automatic validation.

    Features:
    - Validates all required environment variables on startup
    - Type checking (int, bool, URL, etc.)
    - Validation rules (min/max, regex patterns)
    - Clear error messages for invalid configuration
    - Fail-fast behavior (app won't start with invalid config)

    Environment variables are loaded from:
    1. .env file (if exists)
    2. System environment variables
    3. Default values (for optional vars)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore unknown env vars
    )

    # ===================
    # JWT Configuration
    # ===================
    JWT_SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="JWT secret key (MUST be changed in production, min 32 chars)"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        pattern="^(HS256|HS384|HS512|RS256|RS384|RS512)$",
        description="JWT signing algorithm"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=5,
        le=1440,  # Max 24 hours
        description="Access token expiration in minutes (5-1440)"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        le=90,  # Max 90 days
        description="Refresh token expiration in days (1-90)"
    )

    # ===================
    # Database Configuration
    # ===================
    DB_HOST: str = Field(
        default="localhost",
        description="Database host"
    )
    DB_PORT: int = Field(
        default=5432,
        ge=1,
        le=65535,
        description="Database port (1-65535)"
    )
    DB_NAME: str = Field(
        ...,
        min_length=1,
        description="Database name (required)"
    )
    DB_USER: str = Field(
        ...,
        min_length=1,
        description="Database user (required)"
    )
    DB_PASSWORD: str = Field(
        ...,
        min_length=1,
        description="Database password (required)"
    )

    # ===================
    # Redis Configuration
    # ===================
    REDIS_HOST: str = Field(
        default="redis",
        description="Redis host"
    )
    REDIS_PORT: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="Redis port (1-65535)"
    )
    REDIS_DB: int = Field(
        default=0,
        ge=0,
        le=15,
        description="Redis database number (0-15)"
    )
    REDIS_PASSWORD: Optional[str] = Field(
        default=None,
        description="Redis password (recommended for production)"
    )

    # ===================
    # Application Configuration
    # ===================
    APP_HOST: str = Field(
        default="0.0.0.0",
        description="Application host"
    )
    APP_PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Application port (1-65535)"
    )
    DEBUG: bool = Field(
        default=False,
        description="Debug mode (should be False in production)"
    )
    ENVIRONMENT: str = Field(
        default="development",
        pattern="^(development|staging|production)$",
        description="Environment name (development|staging|production)"
    )
    SEED_DATABASE: bool = Field(
        default=True,
        description="Seed database with test data on startup"
    )

    # ===================
    # CORS Configuration
    # ===================
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:5173",
        description="Comma-separated list of allowed CORS origins"
    )

    # ===================
    # Email Configuration
    # ===================
    SMTP_HOST: str = Field(
        default="mailpit",
        description="SMTP server host"
    )
    SMTP_PORT: int = Field(
        default=1025,
        ge=1,
        le=65535,
        description="SMTP server port (1-65535)"
    )
    SMTP_USERNAME: Optional[str] = Field(
        default=None,
        description="SMTP username (optional)"
    )
    SMTP_PASSWORD: Optional[str] = Field(
        default=None,
        description="SMTP password (optional)"
    )
    SMTP_USE_TLS: bool = Field(
        default=False,
        description="Use TLS for SMTP connection"
    )
    FROM_EMAIL: str = Field(
        default="noreply@multipult.dev",
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        description="From email address (must be valid email)"
    )
    FRONTEND_URL: str = Field(
        default="http://localhost:5173",
        pattern=r"^https?://.*",
        description="Frontend URL for email links (must start with http:// or https://)"
    )

    # ===================
    # OAuth Configuration
    # ===================
    GOOGLE_CLIENT_ID: Optional[str] = Field(
        default=None,
        description="Google OAuth Client ID (optional)"
    )
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(
        default=None,
        description="Google OAuth Client Secret (optional)"
    )
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(
        default=None,
        description="Telegram Bot Token (optional)"
    )

    # ===================
    # File Upload Configuration
    # ===================
    UPLOAD_DIR: str = Field(
        default="uploads",
        description="Directory for storing uploaded files"
    )
    EXPORT_DIR: str = Field(
        default="exports",
        description="Directory for storing exported files"
    )

    # ===================
    # Sentry Configuration
    # ===================
    SENTRY_DSN: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking (leave empty to disable)"
    )
    SENTRY_ENABLE_TRACING: bool = Field(
        default=True,
        description="Enable Sentry performance tracing"
    )
    SENTRY_TRACES_SAMPLE_RATE: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Sentry traces sample rate (0.0-1.0)"
    )
    SENTRY_RELEASE: Optional[str] = Field(
        default=None,
        description="Sentry release version (optional)"
    )
    SENTRY_DEBUG: bool = Field(
        default=False,
        description="Enable Sentry SDK debug mode"
    )

    # ===================
    # Shutdown Configuration
    # ===================
    SHUTDOWN_TIMEOUT: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Graceful shutdown timeout in seconds (1-300)"
    )

    # ===================
    # Validators
    # ===================

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Ensure JWT secret is strong enough"""
        if "change-in-production" in v.lower() or "your-secret" in v.lower():
            raise ValueError(
                "JWT_SECRET_KEY must be changed from default value in production! "
                "Generate a strong secret with: openssl rand -hex 32"
            )
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters long for security"
            )
        return v

    @field_validator("REDIS_PASSWORD")
    @classmethod
    def validate_redis_password(cls, v: Optional[str], info) -> Optional[str]:
        """Warn if Redis password is not set in production"""
        environment = info.data.get("ENVIRONMENT", "development")
        if environment == "production" and not v:
            import warnings
            warnings.warn(
                "REDIS_PASSWORD is not set in production environment. "
                "Consider setting a password for better security.",
                UserWarning
            )
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Validate production-specific requirements"""
        if self.ENVIRONMENT == "production":
            # Check DEBUG mode
            if self.DEBUG:
                raise ValueError(
                    "DEBUG must be False in production environment for security reasons"
                )

            # Check SEED_DATABASE
            if self.SEED_DATABASE:
                import warnings
                warnings.warn(
                    "SEED_DATABASE is True in production. "
                    "Set to False to prevent seeding production database.",
                    UserWarning
                )

            # Check SMTP configuration for production
            if self.SMTP_HOST == "mailpit":
                raise ValueError(
                    "SMTP_HOST is 'mailpit' in production. "
                    "Configure a real SMTP server for production."
                )

        return self

    # ===================
    # Computed Properties
    # ===================

    @property
    def database_url(self) -> str:
        """Construct database URL from components"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def redis_url(self) -> str:
        """Construct Redis URL from components"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT == "development"


# ===================
# Global Settings Instance
# ===================

# Singleton instance - loaded once on import
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get validated settings instance.

    This function loads and validates environment configuration on first call.
    Subsequent calls return the cached instance.

    Raises:
        ValidationError: If environment configuration is invalid
        SystemExit: If configuration validation fails (fail-fast)

    Returns:
        Settings: Validated settings instance
    """
    global _settings

    if _settings is None:
        try:
            _settings = Settings()
        except ValidationError as e:
            # Print detailed validation errors
            print("\n" + "="*80)
            print("❌ CONFIGURATION VALIDATION FAILED")
            print("="*80)
            print("\nThe following environment variables are invalid:\n")

            for error in e.errors():
                field = " -> ".join(str(loc) for loc in error["loc"])
                msg = error["msg"]
                value = error.get("input", "NOT SET")

                print(f"  ❌ {field}")
                print(f"     Error: {msg}")
                print(f"     Value: {value}")
                print()

            print("="*80)
            print("Please fix the configuration in .env file and restart the application.")
            print("See .env.example for reference.")
            print("="*80 + "\n")

            # Fail-fast: exit immediately with error code
            raise SystemExit(1) from e

    return _settings


# Convenience: export settings instance
settings = get_settings()


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = get_settings()
        print("✅ Configuration validation successful!")
        print(f"\nEnvironment: {config.ENVIRONMENT}")
        print(f"Debug mode: {config.DEBUG}")
        print(f"Database: {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")
        print(f"Redis: {config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}")
        print(f"Frontend URL: {config.FRONTEND_URL}")
        print(f"SMTP: {config.SMTP_HOST}:{config.SMTP_PORT}")
    except SystemExit:
        print("\n❌ Configuration validation failed. See errors above.")
