# Quick Start Guide

## Development (Local)

### 1. Clone and Setup

```bash
cd packages/backend

# Copy environment template
cp .env.example .env

# No need to edit - defaults work for local development
```

### 2. Start Services

```bash
# Start all services (PostgreSQL, Redis, MailPit, Backend)
docker-compose -f docker-compose.dev.yml up

# Or in background:
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Access Services

- **Backend API**: http://localhost:8000
- **GraphQL Playground**: http://localhost:8000/graphql
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **MailPit UI** (email testing): http://localhost:8025

### 4. Test Login

Default test users (created automatically):

| Username    | Password          | Role      |
|-------------|-------------------|-----------|
| admin       | Admin123!         | admin     |
| moderator   | Moderator123!     | moderator |
| editor      | Editor123!        | editor    |
| testuser    | User123!          | user      |

**GraphQL Login Mutation:**
```graphql
mutation {
  login(username: "admin", password: "Admin123!") {
    accessToken
    refreshToken
    user {
      id
      username
      email
      roles {
        name
      }
    }
  }
}
```

---

## Production (Remote Server)

### Prerequisites

You need the following secrets ready:

1. **JWT Secret** (generate: `openssl rand -hex 32`)
2. **Database credentials** (host, name, user, password)
3. **Redis credentials** (host, password)
4. **SMTP credentials** (for sending emails)
5. **Frontend URL** (your domain)

### Option 1: Quick Deploy (Manual)

```bash
# 1. SSH to your server
ssh user@your-server.com

# 2. Clone repository
git clone https://github.com/yourusername/HumansOntology.git
cd HumansOntology/packages/backend

# 3. Create .env file
cp .env.production.template .env
nano .env

# 4. Fill in ALL required secrets in .env
#    - JWT_SECRET_KEY (generate with: openssl rand -hex 32)
#    - DB_HOST, DB_NAME, DB_USER, DB_PASSWORD
#    - REDIS_HOST, REDIS_PASSWORD
#    - SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD
#    - FRONTEND_URL, ALLOWED_ORIGINS

# 5. Validate configuration
python cli.py validate-config

# 6. Build and start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 7. Run database migrations
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head

# 8. Create admin user
docker-compose -f docker-compose.prod.yml exec app python cli.py create-user \
  --username admin \
  --email admin@yourdomain.com \
  --password "YourStrongPassword123!" \
  --role admin \
  --verified

# 9. Check health
curl http://localhost:8000/health
```

### Option 2: GitHub Actions (Automated)

See detailed guide in **[PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md#method-1-github-secrets-recommended-for-github-hosted-repos)**

**Quick Setup:**

1. Add secrets to GitHub repository (Settings → Secrets → Actions)
2. Create `.github/workflows/deploy.yml` (see PRODUCTION_DEPLOYMENT.md)
3. Push to main branch → Automatic deployment

**Required GitHub Secrets:**
```
JWT_SECRET_KEY
DB_HOST, DB_NAME, DB_USER, DB_PASSWORD
REDIS_HOST, REDIS_PASSWORD
SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD
FROM_EMAIL
FRONTEND_URL, ALLOWED_ORIGINS
```

---

## CLI Tool Commands

```bash
# Create user
python cli.py create-user --username admin --email admin@example.com

# Assign role
python cli.py assign-role --user-id 1 --role admin

# Seed database
python cli.py seed-data

# Backup database
python cli.py backup-db --output backup.sql

# Restore database
python cli.py restore-db --input backup.sql --confirm

# Validate config
python cli.py validate-config

# Show config (with secrets masked)
python cli.py show-config

# Health check
python cli.py health-check

# Database stats
python cli.py stats

# Show all commands
python cli.py --help
```

---

## File Structure (Dev vs Prod)

### Development Files
```
packages/backend/
├── .env                          # Local development config (git-ignored)
├── docker-compose.dev.yml        # Development services (MailPit, hot-reload)
└── Dockerfile (target: development)
```

### Production Files
```
packages/backend/
├── .env                          # Generated from secrets (git-ignored)
├── .env.production.template      # Template with placeholders
├── docker-compose.prod.yml       # Production services (Nginx, workers)
├── scripts/generate_env.sh       # Script to generate .env from secrets
├── Dockerfile (target: production)
└── PRODUCTION_DEPLOYMENT.md      # Detailed deployment guide
```

### Configuration Files
```
packages/backend/
├── .env.example                  # Example for development
├── .env.production.template      # Template for production
├── .dockerignore                 # Exclude files from Docker build
└── core/config.py                # Environment validation (auto-validates on startup)
```

---

## Next Steps

### For Development:
- Read [CLAUDE.md](CLAUDE.md) - Project overview and architecture
- Read [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) - Development workflow
- Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- Read [docs/PATTERNS.md](docs/PATTERNS.md) - Code patterns and conventions

### For Production:
- Read [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - Complete deployment guide
- Setup monitoring (Prometheus + Grafana)
- Setup error tracking (Sentry)
- Setup backups (database + files)
- Configure SSL/TLS certificates
- Configure firewall rules

---

## Troubleshooting

### Port already in use
```bash
# Check what's using the port
lsof -i :8000  # or netstat -ano | findstr :8000 on Windows

# Kill process or change port in docker-compose.yml
```

### Database connection failed
```bash
# Check database container
docker-compose -f docker-compose.dev.yml logs db

# Wait for database to be ready (healthcheck)
docker-compose -f docker-compose.dev.yml ps
```

### Configuration validation failed
```bash
# Check configuration errors
python cli.py validate-config

# Common issues:
# - JWT_SECRET_KEY too short (<32 chars)
# - Missing required variables
# - Invalid email format
```

### Container crashes on startup
```bash
# Check logs
docker-compose -f docker-compose.dev.yml logs app

# Common issues:
# - Configuration validation failed
# - Database not ready (wait for healthcheck)
# - Port already in use
```

---

## Support

- **Full Documentation**: See [CLAUDE.md](CLAUDE.md) and [docs/](docs/) directory
- **Production Deployment**: See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
- **Issues**: Check logs with `docker-compose logs -f app`
