# ==============================================================================
# Multi-Stage Docker Build for МультиПУЛЬТ Backend
# Task: #51 - Docker Multi-Stage Build Optimization
# ==============================================================================
#
# This Dockerfile uses multi-stage build to:
# - Reduce final image size from ~500MB to <200MB
# - Separate build dependencies from runtime dependencies
# - Optimize layer caching for faster rebuilds
# - Improve security by minimizing attack surface
#
# Usage:
#   Development: docker-compose -f docker-compose.dev.yml up
#   Production:  docker-compose -f docker-compose.prod.yml up
# ==============================================================================

# ==============================================================================
# Stage 1: Builder
# ==============================================================================
FROM python:3.11-slim AS builder

LABEL stage=builder
LABEL description="Build stage with all dependencies"

WORKDIR /build

# Install build dependencies
# These are needed for compiling Python packages but not for running them
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
# Docker will cache this layer if requirements.txt hasn't changed
COPY requirements.txt .

# Create virtual environment and install dependencies
# Using venv ensures clean dependency isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
# --no-cache-dir: Don't cache pip downloads (saves space)
# --upgrade pip: Use latest pip for better dependency resolution
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# Stage 2: Runtime (Production)
# ==============================================================================
FROM python:3.11-slim AS production

LABEL maintainer="МультиПУЛЬТ Team"
LABEL description="Production-ready backend with GraphQL API"
LABEL version="1.0.0"

# Set environment variables
# PYTHONUNBUFFERED: Ensure Python output is sent straight to terminal (no buffering)
# PYTHONDONTWRITEBYTECODE: Don't create .pyc files (saves space and build time)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install only runtime dependencies (no build tools!)
# libpq5: PostgreSQL client library
# postgresql-client: psql CLI tool for debugging
# ca-certificates: SSL certificates for HTTPS requests
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
# This includes all installed Python packages
COPY --from=builder /opt/venv /opt/venv

# Copy application code
# Using .dockerignore to exclude unnecessary files
COPY . .

# Create necessary directories with proper permissions
# uploads: For user-uploaded files
# exports: For data export files
# logs: For application logs (if file logging enabled)
RUN mkdir -p /app/uploads /app/exports /app/logs && \
    chmod 755 /app/uploads /app/exports /app/logs

# Create non-root user for security
# Running as root is a security risk
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1001 -s /bin/bash appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8000

# Health check
# This helps orchestrators (Docker Compose, Kubernetes) know if container is healthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Default command: Run application with uvicorn
# Override this in docker-compose for different configurations
CMD ["python", "app.py"]

# ==============================================================================
# Stage 3: Development
# ==============================================================================
FROM production AS development

LABEL stage=development
LABEL description="Development stage with hot-reload and debugging tools"

# Switch back to root to install dev tools
USER root

# Install development tools
# watchfiles: For hot-reload during development
# ipdb: Interactive debugger
RUN pip install --no-cache-dir watchfiles ipdb

# Install additional debugging tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    curl \
    wget \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Development-specific directories
RUN mkdir -p /app/test-data && \
    chown -R appuser:appuser /app

# Switch back to non-root user
USER appuser

# Development command: Run with auto-reload
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
