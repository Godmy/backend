# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Soft Delete Functionality** - Applied SoftDeleteMixin to core models
  - `UserModel`, `ConceptModel`, `DictionaryModel`, `LanguageModel` now support soft delete
  - Records marked with `deleted_at` timestamp instead of hard deletion
  - Automatic filtering of deleted records via default query scopes
  - `restore()` method to undelete records
  - Mixins available at `core/models/mixins/soft_delete.py`

- **Enhanced Health Checks** - Comprehensive system monitoring
  - `core/services/health_service.py` - HealthCheckService for component monitoring
  - New `/health/detailed` endpoint with comprehensive status checks:
    - Database connectivity and response time
    - Redis connectivity and response time
    - Disk space usage monitoring (warning at 90%)
    - Memory usage monitoring (warning at 90%)
  - Overall status: `healthy`, `degraded`, or `unhealthy`
  - Backward-compatible `/health` endpoint maintained
  - Appropriate HTTP status codes (200, 503)

### Changed
- `auth/models/user.py` - Now inherits from `SoftDeleteMixin`
- `languages/models/concept.py` - Now inherits from `SoftDeleteMixin`
- `languages/models/dictionary.py` - Now inherits from `SoftDeleteMixin`
- `languages/models/language.py` - Now inherits from `SoftDeleteMixin`
- `app.py` - Added `/health/detailed` endpoint

### Planned
- Advanced Search & Filtering (P1)
- User Profile Management enhancements (P1)
- API Rate Limiting (P1)
- Import/Export System (P1)

## [0.3.0] - 2025-01-16

### Added - File Upload System
- **File Upload System** with secure storage and validation
  - `core/models/file.py` - File model with metadata (filename, size, MIME type, dimensions)
  - `core/file_storage.py` - FileStorageService for filesystem operations
  - `core/services/file_service.py` - Business logic for file management
  - `core/schemas/file.py` - GraphQL API (uploadAvatar, uploadFile, deleteFile, myFiles)
  - Automatic thumbnail generation (256x256) using Pillow
  - Filename sanitization and path traversal protection
  - Size limits: 5MB for avatars, 10MB for other files
  - MIME type validation (PNG, JPG, GIF, WEBP)
  - `/uploads/{filename:path}` endpoint for serving files
  - Integration with user profiles (avatar_file_id)

### Added - Audit Logging System
- **Comprehensive Audit Logging** for security and compliance
  - `core/models/audit_log.py` - AuditLog model with full action tracking
  - `core/services/audit_service.py` - AuditService with specialized logging methods
  - `core/schemas/audit.py` - GraphQL API (auditLogs, myAuditLogs, userActivity)
  - Support for logging:
    - Authentication events (login, logout, register, OAuth)
    - Entity CRUD operations (create, update, delete)
    - User actions (password change, email change, file upload)
  - IP address and User-Agent capture
  - Before/after data snapshots (JSON)
  - Filtering by user, action, entity type, status, date range
  - Pagination and activity statistics
  - Automatic cleanup method for old logs

### Added - Infrastructure
- **Pillow** dependency for image processing
- **GraphQL Context Authentication** - automatic user extraction from JWT tokens
  - Custom `GraphQLWithContext` class in app.py
  - Automatic user and database session injection into context
- Docker volume for uploads directory
- `UPLOAD_DIR` environment variable

### Added - Documentation
- **TESTING_GUIDE.md** - comprehensive testing guide with examples
  - GraphQL Playground examples
  - cURL examples
  - Python examples
  - Troubleshooting section
  - Database inspection commands
- **CHANGELOG.md** - this file
- Updated **CLAUDE.md** with File Upload and Audit Logging sections
- Updated **ARCHITECTURE.md** with new models and relationships
- Updated **README.md** with new features and examples
- Updated **BACKLOG.md** - marked P0 tasks #1 and #4 as completed

### Changed
- `core/init_db.py` - updated model import order (auth models first)
- `auth/models/profile.py` - added avatar_file_id field
- `core/schemas/schema.py` - integrated FileQuery, FileMutation, AuditLogQuery
- `.env.example` - added UPLOAD_DIR variable
- `docker-compose.dev.yml` - added uploads volume and UPLOAD_DIR env var
- `requirements.txt` - added Pillow library

### Fixed
- Model import order in `core/init_db.py` to prevent circular dependencies
- GraphQL context setup for proper JWT authentication
- File model relationship to UserModel (correct class name)

## [0.2.0] - 2025-01-15

### Added - OAuth Authentication
- **Google OAuth 2.0** integration
  - `auth/services/oauth_service.py` - OAuthService for provider authentication
  - `loginWithGoogle` GraphQL mutation
  - Automatic user creation/linking by email
  - Token verification with Google APIs
- **Telegram Login Widget** integration
  - `loginWithTelegram` GraphQL mutation
  - HMAC signature verification for security
  - Bot token configuration
- `auth/models/oauth.py` - OAuthConnection model for provider links
- OAuth users automatically marked as verified
- Support for multiple OAuth providers per user

### Added - Email Verification
- **Email Verification System** with Redis-backed tokens
  - `core/redis_client.py` - Redis client for token storage
  - `auth/services/token_service.py` - TokenService for verification/reset tokens
  - `verifyEmail` GraphQL mutation
  - 24-hour token TTL
  - Rate limiting (3 emails per hour)
- **Password Reset Flow**
  - `requestPasswordReset` GraphQL mutation
  - `resetPassword` GraphQL mutation
  - 1-hour token TTL
  - Email templates with Jinja2
- **Email Service** integration
  - `core/email_service.py` - EmailService with SMTP
  - HTML/text email templates in `templates/emails/`
  - MailPit for development testing (port 8025)
  - Support for production SMTP (SendGrid, AWS SES)

### Added - Testing Infrastructure
- `tests/test_oauth.py` - OAuth integration tests
- `tests/test_email_service.py` - Email service tests
- `tests/test_email_verification.py` - Verification flow tests
- MailPit Docker container for email testing
- `docker-compose.dev.yml` - development environment with MailPit

### Added - Documentation
- **docs/OAUTH_SETUP.md** - OAuth provider setup guide
- **docs/EMAIL_VERIFICATION_FLOW.md** - email verification documentation
- **MAILPIT_IMPLEMENTATION.md** - MailPit integration guide
- **EMAIL_VERIFICATION_IMPLEMENTATION.md** - technical implementation details

### Changed
- `.env.example` - added OAuth and email configuration
- `auth/models/user.py` - added is_verified field
- `auth/models/profile.py` - enhanced with oauth_connections relationship
- Updated **CLAUDE.md** with OAuth and Email sections
- Updated **README.md** with OAuth and Email features

## [0.1.0] - 2025-01-10

### Added - Initial Release
- **Core Infrastructure**
  - FastAPI/Starlette web framework
  - Strawberry GraphQL server
  - SQLAlchemy ORM with PostgreSQL
  - Alembic database migrations
  - Docker & Docker Compose setup
  - Health check endpoint (`/health`)

- **Authentication & Authorization**
  - JWT-based authentication (access + refresh tokens)
  - `auth/` module with User, Role, Permission models
  - User registration and login
  - Role-based access control (RBAC)
  - Password hashing with bcrypt
  - GraphQL mutations: register, login, refreshToken, logout

- **User Management**
  - User profiles with customizable fields
  - Role assignment (admin, moderator, editor, user)
  - Permission system for granular access control
  - User queries: me, users, user

- **Languages Module**
  - Multi-language support (8 languages: ru, en, es, fr, de, zh, ja, ar)
  - Hierarchical concept structure with materialized path
  - Dictionary for translations (concept ↔ language)
  - GraphQL CRUD for languages, concepts, dictionaries

- **Database**
  - Automatic initialization and table creation
  - Idempotent seed script with test data
  - 5 pre-configured roles with detailed permissions
  - 5 test user accounts
  - ~80 hierarchical concepts
  - ~150 dictionary translations

- **Development Tools**
  - Pre-commit hooks (black, isort, flake8, mypy)
  - pytest test suite with async support
  - GitHub Actions CI/CD pipeline
  - CORS configuration for frontend integration

- **Documentation**
  - **README.md** - main documentation
  - **CLAUDE.md** - Claude Code development guide
  - **ARCHITECTURE.md** - project architecture
  - **DEPLOYMENT.md** - deployment guide
  - **CONTRIBUTING.md** - contribution guidelines
  - **docs/QUICK_START.md** - quick start guide
  - **docs/graphql-examples.md** - GraphQL examples

### Configuration
- Environment variables via `.env` file
- Example configurations for development and production
- Configurable JWT token expiration
- Database connection settings
- CORS origins configuration
- Debug mode toggle

## Version History

- **0.3.0** (2025-01-16) - File Upload & Audit Logging
- **0.2.0** (2025-01-15) - OAuth & Email Verification
- **0.1.0** (2025-01-10) - Initial Release

---

## Legend

- **Added** - New features
- **Changed** - Changes to existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Security improvements

## Links

- [BACKLOG.md](BACKLOG.md) - Planned features and user stories
- [README.md](README.md) - Main documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture overview
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
