# Deployment Guide

Complete guide for deploying your application to production.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Option 1: VPS/Dedicated Server with Nginx](#option-1-vpsdedicated-server-with-nginx)
- [Option 2: Cloud Platform (AWS/GCP/Azure)](#option-2-cloud-platform)
- [Option 3: Docker without Nginx](#option-3-docker-without-nginx)
- [SSL/HTTPS Setup](#sslhttps-setup)
- [Environment Configuration](#environment-configuration)
- [Database Migration](#database-migration)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)

---

## Prerequisites

- Domain name configured (DNS pointing to your server)
- SSH access to server (if using VPS)
- Docker and Docker Compose installed
- SSL certificate (Let's Encrypt recommended)

---

## Deployment Options

### When to use Nginx?

| Scenario | Use Nginx? | Reason |
|----------|-----------|---------|
| **VPS/Dedicated Server** | ✅ YES | Full control, SSL termination, rate limiting |
| **AWS/GCP with Load Balancer** | ❌ NO | Cloud LB handles SSL, routing |
| **Simple/Small Project** | 🤷 OPTIONAL | Simpler but less features |
| **Multiple Uvicorn Workers** | ✅ YES | Load balancing across workers |
| **Static File Serving** | ✅ YES | Nginx serves static files efficiently |

---

## Option 1: VPS/Dedicated Server with Nginx

**Best for**: DigitalOcean, Linode, Hetzner, your own server

### Step 1: Prepare Server

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Step 2: Clone Repository

```bash
# Clone your repository
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo/backend
```

### Step 3: Configure Environment

```bash
# Copy production env template
cp .env.production .env

# Edit with your values
nano .env
```

**IMPORTANT**: Update these values:

```env
# Generate strong JWT secret
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Set strong passwords
DB_PASSWORD=your_strong_db_password
REDIS_PASSWORD=your_strong_redis_password

# Update domain
ALLOWED_ORIGINS=https://yourdomain.com
FRONTEND_URL=https://yourdomain.com

# Configure SMTP (SendGrid/AWS SES)
SMTP_HOST=smtp.sendgrid.net
SMTP_PASSWORD=your_sendgrid_api_key

# OAuth credentials
GOOGLE_CLIENT_ID=your_google_client_id
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

### Step 4: Setup SSL Certificate

```bash
# Install certbot
sudo apt-get install certbot

# Stop any service using port 80
sudo systemctl stop nginx || true

# Generate certificate
sudo certbot certonly --standalone \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --agree-tos \
  --email your-email@example.com

# Certificates will be at:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### Step 5: Update nginx.conf

```bash
# Edit nginx config
nano nginx/nginx.conf
```

Update:
```nginx
server_name yourdomain.com www.yourdomain.com;

ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
```

### Step 6: Update docker-compose.prod.yml

```yaml
nginx:
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro  # Add this
```

### Step 7: Run Database Migrations

```bash
# Build and start database only
docker-compose -f docker-compose.prod.yml up -d db redis

# Wait for DB to be ready
sleep 10

# Run migrations
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head
```

### Step 8: Start Application

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Verify services are running
docker-compose -f docker-compose.prod.yml ps
```

### Step 9: Test Deployment

```bash
# Test HTTP (should redirect to HTTPS)
curl -I http://yourdomain.com/health

# Test HTTPS
curl -I https://yourdomain.com/health

# Test GraphQL endpoint
curl -X POST https://yourdomain.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { queryType { name } } }"}'
```

### Step 10: Setup Auto-renewal for SSL

```bash
# Test renewal
sudo certbot renew --dry-run

# Setup cron job for auto-renewal
sudo crontab -e

# Add this line (renew twice daily)
0 0,12 * * * certbot renew --quiet --post-hook "docker-compose -f /path/to/docker-compose.prod.yml exec nginx nginx -s reload"
```

---

## Option 2: Cloud Platform

### AWS Deployment

#### Architecture:
```
Internet → ALB (SSL) → ECS/EC2 → RDS (PostgreSQL) → ElastiCache (Redis)
```

**You DON'T need nginx** because AWS ALB handles:
- SSL termination
- Load balancing
- Health checks
- Rate limiting (AWS WAF)

#### Setup:

1. **RDS PostgreSQL**
   ```bash
   # Create RDS instance
   aws rds create-db-instance \
     --db-instance-identifier yourapp-db \
     --db-instance-class db.t3.micro \
     --engine postgres \
     --master-username admin \
     --master-user-password YourStrongPassword
   ```

2. **ElastiCache Redis**
   ```bash
   aws elasticache create-cache-cluster \
     --cache-cluster-id yourapp-redis \
     --cache-node-type cache.t3.micro \
     --engine redis \
     --num-cache-nodes 1
   ```

3. **ECS (Fargate)**
   - Push Docker image to ECR
   - Create ECS task definition
   - Create ECS service
   - Configure ALB target group

4. **Environment Variables**
   - Store in AWS Systems Manager Parameter Store or Secrets Manager
   - Reference in ECS task definition

### Google Cloud Platform

#### Architecture:
```
Internet → Cloud Load Balancer → Cloud Run → Cloud SQL (PostgreSQL) → Memorystore (Redis)
```

**You DON'T need nginx** - Cloud Load Balancer handles everything.

#### Setup:

```bash
# Deploy to Cloud Run
gcloud run deploy yourapp \
  --image gcr.io/your-project/yourapp \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$DATABASE_URL,REDIS_HOST=$REDIS_HOST
```

---

## Option 3: Docker without Nginx

**Use when**: Simple project, cloud load balancer available, or testing

### docker-compose.simple.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    command: uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
    ports:
      - "8000:8000"  # Expose directly
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_HOST=redis
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Deploy:

```bash
docker-compose -f docker-compose.simple.yml up -d
```

**Note**: You'll need to handle SSL elsewhere (cloud load balancer, Cloudflare, etc.)

---

## SSL/HTTPS Setup

### Let's Encrypt (Free)

```bash
# Standalone mode (before nginx starts)
sudo certbot certonly --standalone -d yourdomain.com

# Webroot mode (nginx already running)
sudo certbot certonly --webroot -w /var/www/certbot -d yourdomain.com
```

### Cloudflare (Free SSL)

1. Add domain to Cloudflare
2. Update nameservers
3. Enable SSL/TLS → Full (strict)
4. Done! Cloudflare handles SSL

No nginx SSL configuration needed - use HTTP in nginx, Cloudflare handles HTTPS.

### Self-Signed (Development/Testing Only)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem
```

---

## Environment Configuration

### Production Checklist

Before deploying to production:

- [ ] Change `JWT_SECRET_KEY` to random value (`openssl rand -hex 32`)
- [ ] Set strong `DB_PASSWORD` and `REDIS_PASSWORD`
- [ ] Set `SEED_DATABASE=false`
- [ ] Set `DEBUG=False`
- [ ] Configure production SMTP (SendGrid/AWS SES, not MailPit)
- [ ] Update `ALLOWED_ORIGINS` to production domain(s)
- [ ] Setup SSL certificate (Let's Encrypt recommended)
- [ ] Configure OAuth credentials for production
- [ ] Run database migrations
- [ ] Setup backups (database + Redis)
- [ ] Configure monitoring (logs, health checks, alerts)
- [ ] **Configure Sentry error tracking:**
  - [ ] Create Sentry project at sentry.io
  - [ ] Set `SENTRY_DSN` in production environment
  - [ ] Set `ENVIRONMENT=production`
  - [ ] Set `SENTRY_TRACES_SAMPLE_RATE=0.1` (10%)
  - [ ] Configure `SENTRY_RELEASE` for deploy tracking
  - [ ] Setup alerts and notifications in Sentry UI
- [ ] **Configure Prometheus metrics monitoring:**
  - [ ] Setup Prometheus server to scrape `/metrics` endpoint
  - [ ] Configure scrape interval (15s recommended)
  - [ ] Setup Grafana for visualization
  - [ ] Create dashboards for key metrics
  - [ ] Configure alerts for critical thresholds (error rate, latency, memory)
- [ ] Test OAuth flows in production
- [ ] Setup SSL auto-renewal (cron job for certbot)

### Generate Secrets

```bash
# JWT Secret
openssl rand -hex 32

# Database Password
openssl rand -base64 32

# Redis Password
openssl rand -base64 24
```

---

## Database Migration

### Initial Setup

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# Create initial admin user (optional)
docker-compose -f docker-compose.prod.yml run --rm app python scripts/create_admin.py
```

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose -f docker-compose.prod.yml build

# Run new migrations
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

---

## Monitoring & Logging

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f app

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 app
```

### Health Checks

```bash
# Application health
curl https://yourdomain.com/health

# Database connection
docker-compose -f docker-compose.prod.yml exec db psql -U $DB_USER -d $DB_NAME -c "SELECT 1"

# Redis connection
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### Setup Monitoring (Optional)

#### Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus_data:/prometheus

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  volumes:
    - grafana_data:/var/lib/grafana
```

#### Sentry (Error Tracking)

```bash
# Install sentry-sdk
pip install sentry-sdk

# In app.py
import sentry_sdk
sentry_sdk.init(dsn="YOUR_SENTRY_DSN")
```

---

## Backup & Recovery

### Database Backup

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/backup_$TIMESTAMP.sql

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
```

### Setup Cron for Daily Backups

```bash
# Add to crontab
0 2 * * * /path/to/backup.sh
```

### Restore from Backup

```bash
docker-compose -f docker-compose.prod.yml exec -T db psql -U $DB_USER -d $DB_NAME < backup_20250111_020000.sql
```

### Redis Backup

Redis automatically saves to `/data` with AOF enabled:

```yaml
redis:
  command: redis-server --appendonly yes
  volumes:
    - redis_data:/data
```

Backup the volume:

```bash
docker run --rm -v redis_data:/data -v $(pwd):/backup ubuntu tar czf /backup/redis_backup.tar.gz /data
```

---

## Troubleshooting

### Issue: Services won't start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check disk space
df -h

# Check memory
free -h

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

### Issue: Database connection failed

```bash
# Verify DB is running
docker-compose -f docker-compose.prod.yml ps db

# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Test connection manually
docker-compose -f docker-compose.prod.yml exec db psql -U $DB_USER -d $DB_NAME
```

### Issue: High memory usage

```bash
# Check resource usage
docker stats

# Reduce Uvicorn workers in docker-compose.prod.yml
command: uvicorn app:app --host 0.0.0.0 --port 8000 --workers 2
```

---

## Maintenance

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head
```

### Update Dependencies

```bash
# Update requirements.txt
# Then rebuild
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Renew SSL Certificate

```bash
# Manual renewal
sudo certbot renew

# Reload nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

---

## Summary

### With Nginx (Recommended)

✅ Use when:
- Deploying to VPS/dedicated server
- Need full control over SSL, rate limiting, caching
- Serving static files
- Running multiple workers

📋 Steps:
1. Setup SSL with Let's Encrypt
2. Configure nginx.conf
3. Use docker-compose.prod.yml
4. Setup auto-renewal for SSL

### Without Nginx (Cloud)

✅ Use when:
- Using AWS ALB, GCP Load Balancer, Azure App Gateway
- Cloud provider handles SSL and routing
- Simplified deployment

📋 Steps:
1. Deploy to cloud service (ECS, Cloud Run, App Service)
2. Configure cloud load balancer
3. Point DNS to load balancer
4. Cloud handles SSL automatically

Choose based on your infrastructure and requirements!
