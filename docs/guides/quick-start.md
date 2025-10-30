# Quick Start Guide

This guide provides everything you need to get the backend application up and running for both development and production environments.

## 1. Development Setup (Local)

This is the recommended way to run the application for local development. It uses Docker to manage all services, including the database, cache, and a local email testing tool.

### Prerequisites
- Docker and Docker Compose must be installed.

### Steps

1.  **Clone the Repository**
    ```bash
    git clone <your-repo-url>
    cd HumansOntology/packages/backend
    ```

2.  **Configure Environment**
    Copy the example environment file. The default values are pre-configured for local development and require no changes.
    ```bash
    cp .env.example .env
    ```

3.  **Start Services**
    This command starts the backend application, PostgreSQL, Redis, and MailPit in development mode with hot-reloading enabled.
    ```bash
    docker-compose -f docker-compose.dev.yml up
    ```
    To run in the background, add the `-d` flag.

### Accessing Services

Once the containers are running, you can access the following services:

-   **GraphQL API & Playground**: [http://localhost:8000/graphql](http://localhost:8000/graphql)
-   **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
-   **Prometheus Metrics**: [http://localhost:8000/metrics](http://localhost:8000/metrics)
-   **MailPit UI (Email Testing)**: [http://localhost:8025](http://localhost:8025)

### Test Accounts

The database is automatically seeded with test users on first launch:

| Username | Password | Role |
| :--- | :--- | :--- |
| `admin` | `Admin123!` | admin |
| `moderator` | `Moderator123!` | moderator |
| `editor` | `Editor123!` | editor |
| `testuser` | `User123!` | user |

### First GraphQL Query

Use the GraphQL Playground to log in as the admin user:

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

## 2. Production Deployment

For a comprehensive guide on deploying to production, including automated deployments with GitHub Actions, Kubernetes, and advanced secret management, please refer to the **[Full Deployment Guide](./deployment.md)**.

## 3. Using the CLI

The project includes a powerful CLI for administrative tasks. Run commands from within the `app` container or a local shell with an activated virtual environment.

### Common Commands

```bash
# Show all available commands
python cli.py --help

# Create a new user
python cli.py create-user --username newuser --email user@example.com --password "NewPass123!" --role user --verified

# Assign a role to a user
python cli.py assign-role --user-id 1 --role admin

# Validate the .env configuration
python cli.py validate-config

# Check the health of connected services (DB, Redis)
python cli.py health-check

# Display database statistics
python cli.py stats

# Seed the database manually
python cli.py seed-data
```

To run via Docker:
```bash
docker-compose -f docker-compose.prod.yml exec app python cli.py <command>
```

## 4. Project Structure Overview

The backend is organized into modules, with a strict separation of concerns:

-   `packages/backend/`
    -   `alembic/`: Database migrations.
    -   `auth/`: Authentication, authorization, and user management.
    -   `core/`: Core application logic, database setup, base models.
    -   `docs/`: All project documentation.
    -   `languages/`: Models and services for concepts and translations.
    -   `scripts/`: Helper and seeding scripts.
    -   `tests/`: Automated tests.
    -   `app.py`: Main application entrypoint.
    -   `cli.py`: Command-line interface.
    -   `docker-compose.dev.yml`: Docker configuration for development.
    -   `docker-compose.prod.yml`: Docker configuration for production.

For a deeper dive into the project's structure, see the **[Architecture Guide](./architecture.md)**.
