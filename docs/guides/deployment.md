# Production Deployment Guide

This guide provides a comprehensive overview of deploying the application to a production environment. It covers everything from manual single-server setup to automated deployments.

## 1. Configuration & Secrets Management

**CRITICAL:** Before deploying, you must manage your secrets. **Do not commit secrets to Git.**

### Required Secrets

You must define these values in your environment.

-   **`JWT_SECRET_KEY`**: A long, random string. Generate with `openssl rand -hex 32`.
-   **`DB_HOST`**, **`DB_PORT`**, **`DB_NAME`**, **`DB_USER`**, **`DB_PASSWORD`**: Your production database credentials.
-   **`REDIS_HOST`**, **`REDIS_PORT`**, **`REDIS_PASSWORD`**: Your production Redis credentials.
-   **`SMTP_HOST`**, **`SMTP_PORT`**, **`SMTP_USERNAME`**, **`SMTP_PASSWORD`**, **`FROM_EMAIL`**: Production SMTP server details (e.g., SendGrid, AWS SES).
-   **`FRONTEND_URL`**, **`ALLOWED_ORIGINS`**: The URL of your frontend application.
-   **`SENTRY_DSN`** (Recommended): For error tracking in production.

### Configuration Validator

The application has a built-in configuration validator that runs on startup. It will prevent the server from starting with an insecure or incomplete configuration (e.g., `DEBUG=True` in production, default JWT secret, etc.).

To validate your configuration manually:
```bash
docker-compose -f docker-compose.prod.yml exec app python cli.py validate-config
```

## 2. Building the Production Docker Image

The `Dockerfile` uses a multi-stage build to create a small, optimized production image.

-   **`development` stage**: Includes dev dependencies and tools.
-   **`production` stage**: A slim image with only the necessary runtime dependencies.

To build the production image:
```bash
docker build --target production -t your-image-name:latest ./packages/backend
```
This produces an image under 200MB, improving security and deployment speed.

## 3. Deployment Methods

### Method 1: Single Server with Docker Compose & Nginx (Recommended for VPS)

This method uses Nginx as a reverse proxy to handle SSL, caching, and rate limiting, with the application running in Docker.

**Server Architecture:**
`Internet -> Nginx (SSL Termination) -> Uvicorn (in Docker)`

**Steps:**

1.  **Prepare Server**: Install Docker, Docker Compose, and Nginx.

2.  **Clone Repository**:
    ```bash
    git clone <your-repo-url>
    cd your-repo/packages/backend
    ```

3.  **Setup SSL**: Use Certbot to get a free SSL certificate from Let's Encrypt.
    ```bash
    sudo certbot certonly --nginx -d yourdomain.com
    ```

4.  **Configure Nginx**: A production-ready `nginx.conf` is provided in the `nginx/` directory. Update it with your domain and SSL certificate paths.

5.  **Create `.env` file**: Create a `.env` file on the server with your production secrets.

6.  **Deploy**:
    ```bash
    # Build and start all services in the background
    docker-compose -f docker-compose.prod.yml up -d --build

    # Run database migrations
    docker-compose -f docker-compose.prod.yml exec app alembic upgrade head

    # Create an initial admin user
    docker-compose -f docker-compose.prod.yml exec app python cli.py create-user \
      --username admin \
      --email admin@yourdomain.com \
      --password "YourStrongPassword!" \
      --role admin --verified
    ```

7.  **Setup Auto-Renewal**: Configure a cron job to automatically renew your SSL certificate.

### Method 2: Automated Deployment with GitHub Actions

This method automates the entire deployment process whenever you push to the `main` branch.

**Workflow:**
1.  **Push to `main`**: Triggers the GitHub Actions workflow.
2.  **Build & Push Image**: A new Docker image is built and pushed to a container registry (e.g., Docker Hub).
3.  **Deploy to Server**: The workflow SSHes into your server, pulls the new image, generates the `.env` file from GitHub Secrets, runs migrations, and restarts the services.

**Setup:**

1.  **Add Secrets to GitHub**: Go to your repository's **Settings -> Secrets and variables -> Actions** and add all the required secrets listed in section 1.
2.  **Create Workflow File**: Create a `.github/workflows/deploy.yml` file. A complete example is available in the archived `PRODUCTION_DEPLOYMENT.md` file.

### Method 3: Kubernetes (for Scalable Environments)

For large-scale, high-availability deployments, Kubernetes is the recommended approach.

**Setup:**

1.  **Create Kubernetes Secrets**: Store all your secrets (database, JWT, Redis, etc.) as native Kubernetes secrets.
    ```bash
    kubectl create secret generic db-credentials --from-literal=password=...
    ```
2.  **Create Deployment**: Define a `Deployment` object in a YAML file. This will manage the application pods, replicas, and update strategy.
3.  **Create Service**: Define a `Service` to expose the deployment within the cluster.
4.  **Create Ingress**: Define an `Ingress` to expose the service to the internet, manage SSL, and handle routing.

## 4. Post-Deployment

### Health Checks

-   **Liveness Probe**: `GET /health` - Returns `{"status": "ok"}`. Use this for basic container health.
-   **Readiness Probe**: `GET /health/detailed` - Returns status of DB and Redis connections. Use this to determine if the app is ready to accept traffic.

### Monitoring

-   **Logs**: View container logs for errors.
    ```bash
    docker-compose -f docker-compose.prod.yml logs -f app
    ```
-   **Metrics**: Scrape the `/metrics` endpoint with a Prometheus server for detailed application and system metrics.
-   **Error Tracking**: Monitor your Sentry dashboard for real-time exception tracking.

### Database Backups

Regularly back up your database. You can use the built-in CLI command:

```bash
# Create a backup
docker-compose -f docker-compose.prod.yml exec app python cli.py backup-db --output /backups/db.sql

# Restore from a backup
docker-compose -f docker-compose.prod.yml exec app python cli.py restore-db --input /backups/db.sql --confirm
```

Automate this process using a cron job.
