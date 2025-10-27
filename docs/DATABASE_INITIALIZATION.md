# Database Initialization Contexts

This document describes how database initialization works in different contexts and environments.

## Overview

The database initialization system in МультиПУЛЬТ consists of two main steps:

1. **Schema Creation** - Creating tables, indexes, and constraints via `core/init_db.py`
2. **Data Seeding** - Populating initial/test data via `scripts/seed_data.py`

Both steps are idempotent and can be safely run multiple times.

---

## Initialization Contexts

### 1. Application Startup (Production/Development)

**File:** `app.py:39-40`

```python
seed_db = os.getenv("SEED_DATABASE", "true").lower() == "true"
init_database(seed=seed_db)
```

**When it runs:**
- Every time the application starts
- Both when running directly (`python app.py`) and via Docker

**Behavior:**
- Waits for database to be available (max 30 retries, 2s delay)
- Creates all tables if they don't exist
- Optionally seeds data based on `SEED_DATABASE` environment variable

**Configuration:**

| Environment | SEED_DATABASE | Behavior |
|------------|---------------|----------|
| Development | `"true"` | Auto-seeds on startup |
| Production | `"false"` | Only creates schema |

**Docker Compose:**
- `docker-compose.dev.yml` → `SEED_DATABASE: "true"`
- `docker-compose.yml` → `SEED_DATABASE: "false"`
- `docker-compose.prod.yml` → `SEED_DATABASE=false`

---

### 2. CLI Tool (Manual Seeding)

**File:** `cli.py:211-242`

```bash
# Manual seeding via CLI
python cli.py seed-data

# Dry run (shows what would be created)
python cli.py seed-data --dry-run
```

**When to use:**
- Manual database seeding in production
- Testing seeding logic
- Resetting development database

**Behavior:**
- Uses `scripts/seed_data.py:main()`
- Skips existing data (idempotent)
- Shows detailed statistics after completion

**Features:**
- Dry-run mode for testing
- Colored output with success/error messages
- Database statistics reporting

---

### 3. Direct Script Execution

**File:** `scripts/seed_data.py`

```bash
# Use new modular seeder system (recommended)
cd packages/backend
python -m scripts.seed_data

# Or use the new system directly
python -m scripts.seed_data_new
```

**When to use:**
- Development and testing
- Database initialization in CI/CD pipelines
- Custom seeding scenarios

**Behavior:**
- Uses new modular seeder system (`scripts/seeders/`)
- 10x faster for domain concepts
- Automatic dependency resolution
- Detailed progress tracking

**Seeders included:**
- Languages (8 languages)
- Roles & Permissions (5 roles, ~30 permissions)
- Users (5 test users)
- UI Concepts (~200 translations)
- Domain Concepts (~11,000-15,000 attractor concepts)

---

## Components

### core/init_db.py

Main initialization module with three key functions:

#### `wait_for_db(max_retries=30, delay=2)`
Waits for database to become available.

**Parameters:**
- `max_retries` - Maximum connection attempts (default: 30)
- `delay` - Delay between attempts in seconds (default: 2)

**Returns:**
- `True` if connected successfully
- Raises `OperationalError` after max retries

**Usage:**
```python
from core.init_db import wait_for_db

if wait_for_db():
    print("Database is ready!")
```

#### `import_all_models()`
Imports all SQLAlchemy models to register them with `Base.metadata`.

**Models imported (in order):**
1. Auth models (user, role, permission, profile, oauth)
2. Core models (audit_log, file)
3. Languages models (language, concept, dictionary)

**Why order matters:**
Auth models must be imported first because other models reference them via foreign keys.

#### `create_tables()`
Creates all database tables.

**Behavior:**
- Calls `import_all_models()` first
- Uses `Base.metadata.create_all(bind=engine)`
- Idempotent (safe to run multiple times)

#### `init_database(seed=True)`
Main initialization function.

**Parameters:**
- `seed` (bool) - Whether to seed data after creating tables

**Process:**
1. Wait for database (`wait_for_db()`)
2. Create tables (`create_tables()`)
3. Optionally seed data (`scripts.seed_data.main()`)

---

### scripts/seed_data.py

Main seeding script with modular architecture.

**Key function:** `seed_new_system(db)`

Uses the new modular seeder system (`scripts/seeders/`):
- `SeederOrchestrator` - Manages seeder execution order
- Automatic dependency resolution
- Batch processing for performance
- Progress tracking and statistics

**Old functions (deprecated but available):**
- `seed_languages()` - Add 8 languages
- `seed_permissions_and_roles()` - Create RBAC system
- `seed_users()` - Add 5 test users
- `seed_concepts()` - Create concept hierarchy
- `seed_dictionaries()` - Add translations

**Usage:**
```python
from scripts.seed_data import main as seed_main

seed_main()  # Uses new system by default
```

---

## Environment Variables

### SEED_DATABASE

Controls automatic seeding on application startup.

**Values:**
- `"true"` - Enable auto-seeding (development)
- `"false"` - Disable auto-seeding (production)

**Default:** `"true"`

**Where to set:**

1. **Docker Compose:**
   ```yaml
   environment:
     SEED_DATABASE: "true"
   ```

2. **.env file:**
   ```env
   SEED_DATABASE=true
   ```

3. **Command line:**
   ```bash
   SEED_DATABASE=false python app.py
   ```

---

## Best Practices

### Development

✅ **DO:**
- Set `SEED_DATABASE=true` in development
- Use `docker-compose.dev.yml` for local development
- Run `python cli.py seed-data` to reseed manually
- Use `--dry-run` flag to preview changes

❌ **DON'T:**
- Commit changes to production seed data
- Hardcode passwords in seed scripts
- Seed data directly in production environment

### Production

✅ **DO:**
- Set `SEED_DATABASE=false` in production
- Use `python cli.py seed-data` for manual seeding
- Seed initial data during deployment setup
- Use migrations for schema changes

❌ **DON'T:**
- Enable auto-seeding in production
- Run seed scripts without backups
- Seed test users in production

## Troubleshooting

### Database connection fails

**Symptom:** `OperationalError: could not connect to server`

**Solutions:**
1. Check database is running: `docker-compose ps`
2. Verify connection settings in `.env`
3. Increase `max_retries` in `wait_for_db()`
4. Check database logs: `docker-compose logs db`

### Seeding fails with "already exists"

**Symptom:** `IntegrityError: duplicate key value`

**Solutions:**
1. Seeders are idempotent - this is OK
2. Check logs to see what was skipped
3. Drop database and reseed if needed:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

### Tables not created

**Symptom:** `ProgrammingError: relation does not exist`

**Solutions:**
1. Check all models are imported in `init_db.py`
2. Verify import order (auth models first)
3. Run `create_tables()` manually:
   ```python
   from core.init_db import create_tables
   create_tables()
   ```

### Tests fail with import errors

**Symptom:** `ImportError: cannot import name 'User'`

**Solutions:**
2. Check model imports don't have circular dependencies
3. Verify test database is created before tests run

---

## Migration from Old System

If you're upgrading from the old seeding system:

1. **New system is default** - `seed_data.py:main()` uses new system
2. **Old functions still work** - Available for backward compatibility
3. **10x faster** - New system optimized for large datasets
4. **Better architecture** - Follows SOLID principles

**To use old system only:**
```python
# In scripts/seed_data.py
def main():
    db = SessionLocal()
    try:
        seed_languages(db)
        seed_permissions_and_roles(db)
        seed_users(db)
        seed_concepts(db)
        seed_dictionaries(db)
        db.commit()
    finally:
        db.close()
```

---

## Related Documentation

- [Database Seeding System](../scripts/seeders/README.md) - New modular seeder architecture
- [CHANGELOG.md](../CHANGELOG.md#060---2025-01-27) - v0.6.0 seeding system changes
- [PATTERNS.md](PATTERNS.md) - Code patterns and conventions
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Production deployment guide

---

## Summary

| Context | File | When | Seeding | Database |
|---------|------|------|---------|----------|
| Application | `app.py` | Startup | Optional (env) | PostgreSQL |
| CLI Tool | `cli.py` | Manual | Yes | PostgreSQL |
| Direct Script | `seed_data.py` | Manual | Yes | PostgreSQL |

**Key Takeaway:** All contexts use the same underlying functions (`init_database`, `create_tables`, `seed_data.main`), but differ in when and how they're invoked.
