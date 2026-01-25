# Features Documentation

Complete documentation for all МультиПУЛЬТ backend features.

## Table of Contents

### Core Features

#### Health & Monitoring
- **[Health Checks](health_checks.md)** - System health monitoring endpoints
- **[Prometheus Metrics](prometheus.md)** - Application metrics collection and monitoring
- **[Database Pool Monitoring](db_pool_monitoring.md)** - Connection pool health and usage
- **[Request Tracing](request_tracing.md)** - Distributed tracing with request IDs
- **[Request Logging](request_logging.md)** - API request/response logging

#### Authentication & Users
- **[Email Service](email_service.md)** - Email sending with MailPit/SMTP
- **[Email Verification](email_verification.md)** - Email verification and password reset flows
- **[User Profile Management](user_profile.md)** - Profile management, password/email changes
- **[Admin Panel](admin_panel.md)** - User management, system statistics, bulk operations

#### Content Management
- **[File Upload System](file_upload.md)** - Secure file uploads with thumbnails
- **[Advanced Search](search.md)** - Full-text search with filtering and suggestions
- **[Import/Export](import_export.md)** - Data import/export in JSON/CSV/XLSX formats

#### Data Management
- **[Soft Delete](soft_delete.md)** - Soft delete with restore capabilities
- **[Audit Logging](audit_logging.md)** - Comprehensive activity tracking

#### Security & Performance
- **[Security Headers](security_headers.md)** - Security headers middleware
- **[Sentry Error Tracking](sentry.md)** - Error tracking and performance monitoring
- **[Graceful Shutdown](graceful_shutdown.md)** - Graceful application shutdown

---

## Feature Categories

### 🔐 Authentication & Authorization
1. Email Verification & Password Reset
2. User Profile Management
3. Admin Panel Features

### 📊 Monitoring & Observability
1. Health Checks
2. Prometheus Metrics
3. Database Pool Monitoring
4. Request Tracing
5. Request Logging
6. Audit Logging
7. Sentry Error Tracking

### 📁 Content & Files
1. File Upload System
2. Advanced Search & Filtering
3. Import/Export System

### 🛡️ Security
1. Security Headers Middleware
2. Soft Delete System
3. Audit Logging

### ⚙️ Infrastructure
1. Email Service
2. Graceful Shutdown
3. Database Pool Monitoring

---

## Quick Links

### For Developers
- **[GraphQL API](../graphql/README.md)** - Complete API documentation
- **[Architecture Overview](../../CLAUDE.md#architecture)** - System architecture
- **[Testing Guide](../../TESTING_GUIDE.md)** - Testing strategies

### For DevOps
- **[Deployment Guide](../../DEPLOYMENT.md)** - Production deployment
- **[Health Checks](health_checks.md)** - Monitoring setup
- **[Prometheus Metrics](prometheus.md)** - Metrics configuration
- **[Graceful Shutdown](graceful_shutdown.md)** - Shutdown handling

### For Administrators
- **[Admin Panel](admin_panel.md)** - User management
- **[Audit Logging](audit_logging.md)** - Activity tracking
- **[Soft Delete](soft_delete.md)** - Data recovery

---

## Feature Flags

Some features can be enabled/disabled via environment variables:

| Feature | Environment Variable | Default |
|---------|---------------------|---------|
| Email Service | `SMTP_HOST` | Required |
| Sentry | `SENTRY_DSN` | Optional |
| Metrics | Always enabled | - |
| Health Checks | Always enabled | - |
| Security Headers | `SECURITY_HEADERS_ENABLED` | true |
| Request Logging | `REQUEST_LOGGING_ENABLED` | true |

---

## Configuration

All features are configured via `.env` file. See `.env.example` for all available options.

### Quick Start

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env

# Start application
docker-compose -f docker-compose.dev.yml up
```

---

## Contributing

When adding new features:

1. Create feature documentation in `docs/features/`
2. Add to this README in appropriate category
3. Update `CLAUDE.md` with feature link
4. Add configuration options to `.env.example`
5. Write tests in `tests/`
6. Update GraphQL documentation if applicable

---

## Support

- **Issues:** [GitHub Issues](https://github.com/your-org/multipult/issues)
- **Documentation:** See individual feature files
- **API Documentation:** [docs/graphql/README.md](../graphql/README.md)
