# CLAUDE.md — backend

Python GraphQL backend ("МультиПУЛЬТ"/Multipult, v0.6.0). See `packages/CLAUDE.md` for the monorepo-level map; this file is specific to `backend/`.

## Stack
- Python 3.11+, FastAPI/Starlette, GraphQL via Strawberry.
- SQLAlchemy + PostgreSQL, Alembic migrations, Redis (caching + background tasks), Celery (workers/periodic tasks).
- Auth: JWT + OAuth 2.0, RBAC.

## Layout
- `auth/` — models/schemas/services/dependencies/utils for authentication, OAuth, roles, permissions, JWT handling.
- `core/` — app internals: config, database, celery app, structured logging, metrics/tracing/Sentry, middleware (rate limiting, security headers, request logging, cache control), GraphQL context/playground, routes, base models/mixins (soft-delete, tenant, versioned, audit metadata, GDPR).
- `languages/` — concept/dictionary/language domain (models, schemas, services).
- `alembic/` — Alembic env + migration scripts (`alembic.ini` at repo root of this package).
- `scripts/seeders/` — DB seeding orchestrator, per-domain seeders (`auth`, `concepts`, `languages`); `scripts/_deprecated/` holds superseded seed scripts — don't extend those.
- `tasks/`, `workers/` — Celery task definitions and worker entrypoint.
- `tests/` — pytest suite (see Testing below).

## ⚠️ `docs/` is gone — don't trust references to it
The entire `docs/` tree (guides, feature docs, ADRs, `BASE_MODEL_*.md`, scrum backlog/changelog) was deleted by submodule commit `5af656c "ready for use"`; current `HEAD` is several commits past that and `docs/` was never restored. `README.md`, `MAP.md`, and `core/models/ARCHITECTURE.md`/`mixins/README.md` all still link into `docs/...` — those links are dead. Don't read or cite `docs/guides/*`, `docs/features/*`, `docs/BASE_MODEL_*.md`, `docs/scrum/**`, or `docs/project/*` as if they exist; treat the code itself (models, mixins, `alembic/env.py`, `core/platform/db/init_db.py`) as the only source of truth. `MAP.md` is a stale directory dump from before this deletion — don't navigate by it without verifying with `ls`/`Glob` first.
If a real need arises to consult the deleted docs, they're still recoverable from history: `git show 5af656c^:docs/<path>`.

## Testing
- Config in `pytest.ini`: `testpaths = tests`, `asyncio_mode = auto`.
- Markers: `unit` (fast, no external deps), `integration` (needs Docker services like MailPit), `slow` (>1s). Use `-m` to scope runs, e.g. `pytest -m unit`.

## Conventions
- Don't hand-edit generated/derived files.
- For creating/editing DB tables (models, mixins, Alembic migrations, seeders), use the `db-tables` skill — it documents the actual (code-verified) workflow, including the create_all-vs-Alembic split and which mixins are actually used vs. aspirational.
