#!/bin/bash
# ==============================================================================
# Environment File Generator from Secrets
# Task: #28 - Secrets Management
# ==============================================================================
#
# This script generates .env file from environment variables/GitHub Secrets
# during deployment.
#
# Usage:
#   ./scripts/generate_env.sh
#
# In GitHub Actions:
#   - Set secrets in repository settings
#   - Run this script before docker-compose up
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==============================================================================
# Functions
# ==============================================================================

error() {
    echo -e "${RED}✗ $1${NC}" >&2
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

info() {
    echo -e "${NC}ℹ $1${NC}"
}

# Check if required environment variable is set
check_required() {
    local var_name=$1
    local var_value="${!var_name}"

    if [ -z "$var_value" ]; then
        error "Required environment variable $var_name is not set"
        return 1
    fi
    return 0
}

# ==============================================================================
# Main Script
# ==============================================================================

info "Generating production .env file from secrets..."

# Check required secrets
REQUIRED_VARS=(
    "JWT_SECRET_KEY"
    "DB_HOST"
    "DB_NAME"
    "DB_USER"
    "DB_PASSWORD"
    "REDIS_HOST"
    "ALLOWED_ORIGINS"
    "SMTP_HOST"
    "SMTP_USERNAME"
    "SMTP_PASSWORD"
    "FROM_EMAIL"
    "FRONTEND_URL"
)

missing_vars=()
for var in "${REQUIRED_VARS[@]}"; do
    if ! check_required "$var"; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    error "Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        error "  - $var"
    done
    error "Please set these as GitHub Secrets or environment variables"
    exit 1
fi

# Generate .env file from template
info "Generating .env file..."

# Use template or create from scratch
if [ -f ".env.production.template" ]; then
    # Use envsubst to replace placeholders
    envsubst < .env.production.template > .env
    success ".env file generated from template"
else
    warning "Template file not found, creating .env from environment variables"

    # Create .env file directly
    cat > .env << EOF
# Generated automatically on $(date)
# DO NOT EDIT MANUALLY

# JWT
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES:-30}
REFRESH_TOKEN_EXPIRE_DAYS=${REFRESH_TOKEN_EXPIRE_DAYS:-7}

# Database
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}

# Redis
REDIS_HOST=${REDIS_HOST}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_DB=${REDIS_DB:-0}
REDIS_PASSWORD=${REDIS_PASSWORD:-}

# Application
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=False
ENVIRONMENT=production
SEED_DATABASE=false

# CORS
ALLOWED_ORIGINS=${ALLOWED_ORIGINS}

# Email
SMTP_HOST=${SMTP_HOST}
SMTP_PORT=${SMTP_PORT:-587}
SMTP_USERNAME=${SMTP_USERNAME}
SMTP_PASSWORD=${SMTP_PASSWORD}
SMTP_USE_TLS=True
FROM_EMAIL=${FROM_EMAIL}

# Frontend
FRONTEND_URL=${FRONTEND_URL}

# OAuth (optional)
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET:-}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-}

# Uploads
UPLOAD_DIR=uploads
EXPORT_DIR=exports

# Sentry (optional)
SENTRY_DSN=${SENTRY_DSN:-}
SENTRY_ENABLE_TRACING=${SENTRY_ENABLE_TRACING:-true}
SENTRY_TRACES_SAMPLE_RATE=${SENTRY_TRACES_SAMPLE_RATE:-0.1}
SENTRY_RELEASE=${SENTRY_RELEASE:-}
SENTRY_DEBUG=false

# Logging
LOG_LEVEL=${LOG_LEVEL:-INFO}
LOG_FORMAT=json
LOG_DIR=logs
LOG_FILE_ENABLED=false

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_AUTH_PER_MINUTE=${RATE_LIMIT_AUTH_PER_MINUTE:-100}
RATE_LIMIT_ANON_PER_MINUTE=${RATE_LIMIT_ANON_PER_MINUTE:-20}
RATE_LIMIT_WHITELIST_IPS=${RATE_LIMIT_WHITELIST_IPS:-127.0.0.1,::1}
RATE_LIMIT_EXCLUDE_PATHS=/health,/metrics
RATE_LIMIT_ENDPOINT_LIMITS={}

# HTTP Caching
CACHE_CONTROL_ENABLED=true
CACHE_CONTROL_QUERY_MAX_AGE=60
CACHE_CONTROL_DEFAULT_MAX_AGE=30
CACHE_CONTROL_EXCLUDE_PATHS=/metrics

# Shutdown
SHUTDOWN_TIMEOUT=${SHUTDOWN_TIMEOUT:-30}
EOF

    success ".env file created"
fi

# Set proper permissions
chmod 600 .env
success "File permissions set to 600 (owner read/write only)"

# Validate configuration
info "Validating configuration..."
if python cli.py validate-config > /dev/null 2>&1; then
    success "Configuration validation passed"
else
    error "Configuration validation failed"
    error "Check the configuration and try again"
    exit 1
fi

success "Environment file generated successfully!"
info "File location: $(pwd)/.env"
