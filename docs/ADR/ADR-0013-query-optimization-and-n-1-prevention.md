# ADR-0013: Query Optimization & N+1 Prevention

## Status
Accepted

## Context
The application was experiencing performance issues due to inefficient database queries, including slow queries and the N+1 problem in GraphQL resolvers. A comprehensive solution was required to address these issues and improve overall database interaction efficiency.

## Decision
Implement a multi-faceted approach to query optimization and N+1 prevention, including:
1.  **Automatic Query Logging:** Log all database queries in DEBUG mode with timing information.
2.  **Slow Query Detection:** Automatically log queries exceeding a configurable threshold (e.g., 100ms) as warnings.
3.  **Database Indexes:** Add comprehensive indexes to optimize common query patterns on key models (User, Audit Log, File, Dictionary).
4.  **GraphQL DataLoader Integration:** Utilize DataLoaders to batch and cache database queries, preventing N+1 problems in GraphQL resolvers.
5.  **Query Statistics:** Track and log query statistics for various operation types (SELECT, INSERT, UPDATE, DELETE).

## Detailed Implementation

### 1. Automatic Query Logging

All database queries are automatically logged in DEBUG mode with timing information.

**Implementation:** `core/services/query_profiler.py`

```python
# Automatically enabled in core/database.py
from core.services.query_profiler import setup_query_profiling

setup_query_profiling(
    engine,
    enabled=True,
    slow_query_threshold_ms=100,
    log_all_queries=settings.DEBUG
)
```

**Environment Variables:**

```bash
QUERY_PROFILING_ENABLED=true          # Enable/disable profiling
SLOW_QUERY_THRESHOLD_MS=100           # Slow query threshold (ms)
LOG_ALL_QUERIES=false                 # Log all queries in DEBUG mode
```

**Example Log Output:**

```json
{
  "timestamp": "2025-01-27T12:00:00Z",
  "level": "DEBUG",
  "message": "Query (45.23ms): SELECT * FROM users WHERE is_active = true",
  "duration_ms": 45.23,
  "rows": 150
}
```

### 2. Slow Query Detection

Queries exceeding 100ms (configurable) are automatically logged as warnings.

```json
{
  "timestamp": "2025-01-27T12:00:00Z",
  "level": "WARNING",
  "message": "Slow query (234.56ms): SELECT * FROM audit_logs JOIN users...",
  "duration_ms": 234.56,
  "rows": 5000
}
```

### 3. Database Indexes

Comprehensive indexes have been added to optimize common query patterns:

**User Model (`auth/models/user.py`):**
- Single indexes: `username`, `email`, `is_active`, `is_verified`
- Composite indexes:
  - `ix_users_active_verified` - for admin panel filtering
  - `ix_users_deleted_active` - for soft delete queries

**Audit Log Model (`core/models/audit_log.py`):**
- Single indexes: `user_id`, `action`, `entity_type`, `entity_id`, `status`
- Composite indexes:
  - `ix_audit_logs_entity` - entity filtering
  - `ix_audit_logs_user_created` - user activity timeline
  - `ix_audit_logs_action_created` - recent actions
  - `ix_audit_logs_status_created` - failed actions analysis

**File Model (`core/models/file.py`):**
- Single indexes: `mime_type`, `file_type`, `uploaded_by`, `entity_type`, `entity_id`
- Composite indexes:
  - `ix_files_entity` - files by entity
  - `ix_files_user_created` - user's files
  - `ix_files_type_created` - file type filtering

**Dictionary Model (`languages/models/dictionary.py`):**
- Single indexes: `concept_id`, `language_id`, `name`
- Composite indexes:
  - `ix_dictionaries_concept_language` - unique concept-language pair
  - `ix_dictionaries_name` - name search
  - `ix_dictionaries_deleted` - soft delete queries

### 4. GraphQL DataLoader Integration

DataLoaders batch and cache database queries to prevent N+1 problems in GraphQL resolvers.

**Implementation:** `core/services/dataloader.py`

**Usage:**

```python
from core.services.dataloader import get_dataloaders

# In GraphQL context setup
context = {
    "db": db,
    "dataloaders": get_dataloaders(db)
}

# In GraphQL resolver
@strawberry.field
def user(self, info: Info) -> User:
    # Single query for all user IDs in request
    return await info.context["dataloaders"]["user"].load(self.user_id)
```

**Available DataLoaders:**
- `user` - User model with roles and profile
- `role` - Role model
- `concept` - Concept model with creator
- `dictionary` - Dictionary model with concept and language
- `language` - Language model
- `file` - File model with uploader

### 5. Query Statistics

Query statistics are tracked and can be logged:

```python
from core.services.query_profiler import get_query_stats, log_query_stats

# Get statistics
stats = get_query_stats()

# Log statistics
log_query_stats()
```

**Example Output:**

```
Query Statistics:
  SELECT: 1234 queries, avg=15.23ms, max=234.56ms, min=0.12ms, total_rows=45678
  INSERT: 123 queries, avg=8.45ms, max=45.67ms, min=0.89ms, total_rows=123
  UPDATE: 45 queries, avg=12.34ms, max=78.90ms, min=1.23ms, total_rows=45
  DELETE: 12 queries, avg=5.67ms, max=23.45ms, min=0.56ms, total_rows=12
```

## Consequences
- Improved application performance due to reduced query times and elimination of N+1 issues.
- Enhanced observability of database interactions through detailed query logging and statistics.
- Increased development efficiency by providing a structured approach to prevent common performance pitfalls.
- Requires database migration to apply new indexes.
- Introduces new dependencies for query profiling and DataLoader implementation.