# Production Deployment Guide

**Tasks Implemented:**
- #28 - Secrets Management (GitHub Secrets + .env fallback)
- #37 - Environment Configuration Validator
- #49 - CLI Tool для Admin Tasks
- #51 - Docker Multi-Stage Build Optimization

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Secrets Management](#secrets-management)
3. [Docker Build](#docker-build)
4. [Deployment Methods](#deployment-methods)
5. [Post-Deployment](#post-deployment)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- Docker 20.10+
- Docker Compose 2.0+
- Git
- SSH access to production server (for manual deployment)
- GitHub account (for GitHub Actions deployment)

### Required Secrets

You will need to prepare the following secrets before deployment:

#### 1. Database Credentials
```bash
DB_HOST=your-db-host              # e.g., localhost, db.example.com
DB_PORT=5432                       # Default PostgreSQL port
DB_NAME=your-database-name         # e.g., multipult_prod
DB_USER=your-database-user         # e.g., multipult_user
DB_PASSWORD=STRONG_PASSWORD_HERE   # Generate with: openssl rand -base64 32
```

#### 2. JWT Secret (CRITICAL!)
```bash
# Generate with: openssl rand -hex 32
JWT_SECRET_KEY=your-64-character-secret-key-here
```

#### 3. Redis Credentials
```bash
REDIS_HOST=your-redis-host         # e.g., localhost, redis.example.com
REDIS_PORT=6379                    # Default Redis port
REDIS_PASSWORD=STRONG_PASSWORD     # Generate with: openssl rand -base64 32
```

#### 4. Email (SMTP)
```bash
SMTP_HOST=smtp.sendgrid.net        # Your SMTP server
SMTP_PORT=587                      # Usually 587 (TLS) or 465 (SSL)
SMTP_USERNAME=apikey               # Your SMTP username
SMTP_PASSWORD=your-api-key         # Your SMTP password/API key
FROM_EMAIL=noreply@yourdomain.com  # Sender email address
```

**Recommended SMTP providers:**
- SendGrid (12,000 free emails/month)
- AWS SES (62,000 free emails/month first year)
- Mailgun (5,000 free emails/month)
- Postmark (100 free emails/month)

#### 5. Application URLs
```bash
FRONTEND_URL=https://yourdomain.com              # Your frontend URL
ALLOWED_ORIGINS=https://yourdomain.com           # CORS allowed origins (comma-separated)
```

#### 6. Optional: OAuth
```bash
# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your-bot-token
```

#### 7. Optional: Sentry (Recommended for Production)
```bash
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_RELEASE=backend@1.0.0       # Optional: for tracking deploys
```

---

## Secrets Management

### Method 1: GitHub Secrets (Recommended for GitHub-hosted repos)

#### Step 1: Add Secrets to GitHub Repository

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret one by one:

**Required Secrets:**
```
Name: JWT_SECRET_KEY
Value: [Your 64-character secret from: openssl rand -hex 32]

Name: DB_HOST
Value: [Your database host]

Name: DB_NAME
Value: [Your database name]

Name: DB_USER
Value: [Your database user]

Name: DB_PASSWORD
Value: [Your database password]

Name: REDIS_HOST
Value: [Your Redis host]

Name: REDIS_PASSWORD
Value: [Your Redis password]

Name: SMTP_HOST
Value: [Your SMTP server]

Name: SMTP_USERNAME
Value: [Your SMTP username]

Name: SMTP_PASSWORD
Value: [Your SMTP password]

Name: FROM_EMAIL
Value: [Your sender email]

Name: FRONTEND_URL
Value: [Your frontend URL]

Name: ALLOWED_ORIGINS
Value: [Comma-separated list of allowed origins]
```

**Optional Secrets:**
```
Name: GOOGLE_CLIENT_ID
Value: [Your Google OAuth client ID]

Name: GOOGLE_CLIENT_SECRET
Value: [Your Google OAuth client secret]

Name: TELEGRAM_BOT_TOKEN
Value: [Your Telegram bot token]

Name: SENTRY_DSN
Value: [Your Sentry DSN]
```

#### Step 2: Create GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: ./packages/backend
          file: ./packages/backend/Dockerfile
          push: true
          tags: yourusername/multipult-backend:latest
          target: production

      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd /opt/multipult

            # Generate .env from secrets
            export JWT_SECRET_KEY="${{ secrets.JWT_SECRET_KEY }}"
            export DB_HOST="${{ secrets.DB_HOST }}"
            export DB_NAME="${{ secrets.DB_NAME }}"
            export DB_USER="${{ secrets.DB_USER }}"
            export DB_PASSWORD="${{ secrets.DB_PASSWORD }}"
            export REDIS_HOST="${{ secrets.REDIS_HOST }}"
            export REDIS_PASSWORD="${{ secrets.REDIS_PASSWORD }}"
            export SMTP_HOST="${{ secrets.SMTP_HOST }}"
            export SMTP_USERNAME="${{ secrets.SMTP_USERNAME }}"
            export SMTP_PASSWORD="${{ secrets.SMTP_PASSWORD }}"
            export FROM_EMAIL="${{ secrets.FROM_EMAIL }}"
            export FRONTEND_URL="${{ secrets.FRONTEND_URL }}"
            export ALLOWED_ORIGINS="${{ secrets.ALLOWED_ORIGINS }}"

            bash packages/backend/scripts/generate_env.sh

            # Pull latest image
            docker-compose -f docker-compose.prod.yml pull

            # Run migrations
            docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head

            # Restart services
            docker-compose -f docker-compose.prod.yml up -d
```

### Method 2: Manual Deployment with .env File

#### Step 1: Create .env File on Server

SSH to your server and create `.env` file:

```bash
ssh user@your-server.com
cd /opt/multipult/packages/backend

# Copy template
cp .env.production.template .env

# Edit with your secrets
nano .env
```

Fill in all required values in the `.env` file.

#### Step 2: Validate Configuration

```bash
# Validate configuration
python cli.py validate-config

# If validation passes, you'll see:
# ✓ Configuration is valid!
```

---

## Docker Build

### Build Optimized Production Image

```bash
cd packages/backend

# Build production image (multi-stage, optimized)
docker build --target production -t multipult-backend:latest .

# Check image size (should be <200MB)
docker images multipult-backend:latest
```

**Expected output:**
```
REPOSITORY          TAG       IMAGE ID       CREATED         SIZE
multipult-backend   latest    abc123def456   2 minutes ago   185MB
```

### Build Development Image

```bash
# Build development image (includes debugging tools)
docker build --target development -t multipult-backend:dev .
```

---

## Deployment Methods

### Option 1: Docker Compose (Single Server)

#### Step 1: Prepare Server

```bash
# Create application directory
sudo mkdir -p /opt/multipult
cd /opt/multipult

# Clone repository
git clone https://github.com/yourusername/HumansOntology.git .

# Navigate to backend
cd packages/backend
```

#### Step 2: Generate .env File

**Using script (from GitHub Secrets):**
```bash
# Export secrets as environment variables
export JWT_SECRET_KEY="your-secret-here"
export DB_HOST="localhost"
# ... (export all required secrets)

# Generate .env
bash scripts/generate_env.sh
```

**Or manually create .env:**
```bash
cp .env.production.template .env
nano .env
# Fill in all secrets
```

#### Step 3: Deploy

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f app
```

#### Step 4: Run Migrations

```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head
```

#### Step 5: Create Admin User

```bash
# Using CLI tool
docker-compose -f docker-compose.prod.yml exec app python cli.py create-user \
  --username admin \
  --email admin@yourdomain.com \
  --password "YourStrongPassword123!" \
  --role admin \
  --verified
```

### Option 2: Kubernetes (Scalable)

#### Step 1: Create Kubernetes Secrets

```bash
# Create secret for database credentials
kubectl create secret generic db-credentials \
  --from-literal=host=your-db-host \
  --from-literal=name=your-db-name \
  --from-literal=user=your-db-user \
  --from-literal=password=your-db-password

# Create secret for JWT
kubectl create secret generic jwt-secret \
  --from-literal=secret-key=$(openssl rand -hex 32)

# Create secret for Redis
kubectl create secret generic redis-credentials \
  --from-literal=host=your-redis-host \
  --from-literal=password=your-redis-password

# Create secret for SMTP
kubectl create secret generic smtp-credentials \
  --from-literal=host=your-smtp-host \
  --from-literal=username=your-smtp-username \
  --from-literal=password=your-smtp-password \
  --from-literal=from-email=noreply@yourdomain.com
```

#### Step 2: Create Deployment

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multipult-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: multipult-backend
  template:
    metadata:
      labels:
        app: multipult-backend
    spec:
      containers:
      - name: backend
        image: yourusername/multipult-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: host
        - name: DB_NAME
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: name
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: user
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: jwt-secret
              key: secret-key
        # ... (add all other environment variables)
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Step 3: Deploy to Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods
kubectl logs -f deployment/multipult-backend
```

---

## Post-Deployment

### 1. Verify Health

```bash
# Check health endpoint
curl https://yourdomain.com/health

# Expected response:
# {"status": "ok"}

# Check detailed health
curl https://yourdomain.com/health/detailed

# Expected response:
# {
#   "status": "ok",
#   "database": "ok",
#   "redis": "ok",
#   "uptime": 123.45
# }
```

### 2. Verify GraphQL API

```bash
# Open GraphQL Playground
open https://yourdomain.com/graphql

# Test query:
query {
  __schema {
    types {
      name
    }
  }
}
```

### 3. Monitor Logs

```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml logs -f app

# Kubernetes
kubectl logs -f deployment/multipult-backend

# Check for errors
docker-compose -f docker-compose.prod.yml logs app | grep ERROR
```

### 4. Setup Monitoring (Optional but Recommended)

#### Prometheus Metrics

Metrics available at `/metrics`:

```bash
curl https://yourdomain.com/metrics
```

#### Grafana Dashboard

Import pre-built dashboard from `monitoring/grafana-dashboard.json`

#### Sentry Error Tracking

If Sentry is configured, errors will be automatically reported to your Sentry project.

---

## Troubleshooting

### Configuration Validation Failed

```bash
# Run validation manually
docker-compose -f docker-compose.prod.yml exec app python cli.py validate-config

# Common issues:
# - JWT_SECRET_KEY too short (<32 chars)
# - DEBUG=True in production
# - SMTP_HOST=mailpit in production
# - Missing required environment variables
```

### Database Connection Failed

```bash
# Check database connectivity
docker-compose -f docker-compose.prod.yml exec app python cli.py health-check

# Test database connection manually
docker-compose -f docker-compose.prod.yml exec app python -c "
from core.config import get_settings
from sqlalchemy import create_engine
settings = get_settings()
engine = create_engine(settings.database_url)
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('Database OK:', result.scalar())
"
```

### Redis Connection Failed

```bash
# Test Redis connection
docker-compose -f docker-compose.prod.yml exec app python -c "
import redis
from core.config import get_settings
settings = get_settings()
r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD
)
print('Redis OK:', r.ping())
"
```

### Email Not Sending

```bash
# Test SMTP configuration
docker-compose -f docker-compose.prod.yml exec app python -c "
import smtplib
from core.config import get_settings
settings = get_settings()

smtp = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
if settings.SMTP_USE_TLS:
    smtp.starttls()
if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
    smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
print('SMTP connection OK')
smtp.quit()
"
```

### Container Crashes on Startup

```bash
# Check container logs
docker-compose -f docker-compose.prod.yml logs app

# Common issues:
# - Configuration validation failed
# - Database not accessible
# - Port already in use
# - Insufficient permissions

# Run in foreground to see errors
docker-compose -f docker-compose.prod.yml up app
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Reduce workers if needed (edit docker-compose.prod.yml):
# command: uvicorn app:app --host 0.0.0.0 --port 8000 --workers 2
```

---

## Security Checklist

Before going live, ensure:

- [ ] JWT_SECRET_KEY is strong (64+ characters) and unique
- [ ] All passwords are strong (32+ characters)
- [ ] DEBUG=False in production
- [ ] SEED_DATABASE=False in production
- [ ] HTTPS enabled (SSL/TLS certificates)
- [ ] Firewall configured (only necessary ports open)
- [ ] Database accessible only from application server
- [ ] Redis password protected
- [ ] CORS origins limited to your frontend domain
- [ ] Rate limiting enabled
- [ ] Sentry configured for error tracking
- [ ] Backups configured (database + files)
- [ ] Monitoring configured (Prometheus + Grafana)
- [ ] Logs configured (structured JSON logs)

---

## Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head
```

### Backup Database

```bash
# Using CLI tool
docker-compose -f docker-compose.prod.yml exec app python cli.py backup-db --output backup.sql

# Download backup
docker cp $(docker-compose -f docker-compose.prod.yml ps -q app):/app/backup.sql ./backup.sql
```

### Restore Database

```bash
# Upload backup to container
docker cp backup.sql $(docker-compose -f docker-compose.prod.yml ps -q app):/app/

# Restore
docker-compose -f docker-compose.prod.yml exec app python cli.py restore-db --input backup.sql --confirm
```

---

## Support

For issues or questions:
- Check logs: `docker-compose logs -f app`
- Run health check: `python cli.py health-check`
- Validate config: `python cli.py validate-config`
- Check documentation: `docs/` directory
