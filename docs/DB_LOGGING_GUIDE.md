# Database Logging Guide

Comprehensive guide to database logging and statistics tracking in the seeding system.

## Overview

The system now provides detailed logging for all database operations, showing:
- Table record counts before and after operations
- Number of records created/updated/skipped
- Performance metrics (duration, records/second)
- Progress tracking for batch operations
- Visual indicators with emojis for better readability

---

## Components

### 1. core/db_stats.py

Utility module for database statistics tracking.

**Functions:**

#### `get_table_count(db, table_name)`
Get the number of records in a specific table.

```python
from core.db_stats import get_table_count

count = get_table_count(db, "users")
print(f"Users: {count}")
```

#### `get_all_table_counts(db)`
Get record counts for all tables in the database.

```python
from core.db_stats import get_all_table_counts

counts = get_all_table_counts(db)
for table, count in counts.items():
    print(f"{table}: {count}")
```

#### `log_table_statistics(db, tables=None, title="Database Statistics")`
Log formatted table statistics with a title.

```python
from core.db_stats import log_table_statistics

# Log all tables
log_table_statistics(db, title="Current Database State")

# Log specific tables
log_table_statistics(db, ["users", "roles", "permissions"])
```

**Output:**
```
======================================================================
                    Current Database State
======================================================================
  audit_logs                  :        0 records
  concepts                    :   11,234 records
  dictionaries                :    2,456 records
  files                       :        0 records
  languages                   :        8 records
  oauth_connections           :        0 records
  permissions                 :       29 records
  roles                       :        5 records
  user_profiles               :        5 records
  user_roles                  :        5 records
  users                       :        5 records
----------------------------------------------------------------------
  TOTAL                       :   13,747 records
======================================================================
```

#### `log_table_change(table_name, before_count, after_count, created=0, updated=0, skipped=0)`
Log changes in a table with before/after comparison.

```python
from core.db_stats import log_table_change

log_table_change("users", before_count=0, after_count=5, created=5)
```

**Output:**
```
  📊 Table: users
     Before:       0 records
     After:        5 records
     ✅ Created:     5 records
     📈 Delta:      +5 records
```

#### `TableStatsTracker` Class
Track changes across multiple tables during an operation.

```python
from core.db_stats import TableStatsTracker

tracker = TableStatsTracker(db, ["users", "roles"])

# Log before operation
tracker.log_before("Before creating users")

# Perform operations
# ... create users ...

# Log after operation
tracker.log_after("After creating users", created=10, skipped=2)

# Get deltas
delta = tracker.get_delta("users")
total_delta = tracker.get_total_delta()
```

---

### 2. Enhanced BaseSeeder Logging

**Location:** `scripts/seeders/base.py`

#### batch_insert() with logging

**Before:**
```python
# Old output
created = self.batch_insert(LanguageModel, languages_data)
# Output: Progress: 8/8 (100.0%) - languages
```

**After:**
```python
# New output with detailed statistics
created = self.batch_insert(LanguageModel, languages_data)
```

**Output:**
```
  📋 Table: languages
     Records before: 0
     Records to insert: 8
     ✅ Created: 8 records
     Records after: 8
     Delta: +8
```

#### batch_update() with logging

**Output:**
```
  📋 Table: users
     Records in table: 5
     Records to update: 3
     🔄 Updated: 3 records
     Records after: 5
```

---

### 3. SeederOrchestrator Enhanced Summary

**Location:** `scripts/seeders/orchestrator.py`

**Old Summary:**
```
Total seeders: 5
  ✓ Completed: 5
  ⊘ Skipped: 0
  ✗ Failed: 0
  Total records created: 13,742
```

**New Summary:**
```
================================================================================
                              SEEDING SUMMARY
================================================================================
Total seeders: 5
  ✓ Completed: 5
  ⊘ Skipped: 0
  ✗ Failed: 0

Records Statistics:
  ✅ Created:     13,742
  🔄 Updated:          0
  ⊘ Skipped:          0
  📊 Total:       13,742

Duration: 45.32 seconds
Speed: 303 records/second

Details by seeder:
--------------------------------------------------------------------------------
  Status  Name                         Created    Updated    Skipped
--------------------------------------------------------------------------------
  ✓       languages                          8          0          0
  ✓       roles                             34          0          0
  ✓       users                              5          0          0
  ✓       ui_concepts                      203          0          0
  ✓       domain_concepts               13,492          0          0
================================================================================
✓ Seeding completed successfully!
```

---

### 4. Enhanced init_database()

**Location:** `core/init_db.py`

**Output:**
```
======================================================================
                     DATABASE INITIALIZATION
======================================================================

[1/3] Waiting for database connection...
✓ Database connection established

[2/3] Creating database tables...
✓ Database tables created

[3/3] Seeding database with initial data...
----------------------------------------------------------------------
======================================================================
                 Database State BEFORE Seeding
======================================================================
  audit_logs                  :        0 records
  concepts                    :        0 records
  dictionaries                :        0 records
  files                       :        0 records
  languages                   :        0 records
  oauth_connections           :        0 records
  permissions                 :        0 records
  roles                       :        0 records
  user_profiles               :        0 records
  user_roles                  :        0 records
  users                       :        0 records
----------------------------------------------------------------------
  TOTAL                       :        0 records
======================================================================

... (seeding process) ...

======================================================================
                 Database State AFTER Seeding
======================================================================
  audit_logs                  :        0 records
  concepts                    :   11,234 records
  dictionaries                :    2,456 records
  files                       :        0 records
  languages                   :        8 records
  oauth_connections           :        0 records
  permissions                 :       29 records
  roles                       :        5 records
  user_profiles               :        5 records
  user_roles                  :        5 records
  users                       :        5 records
----------------------------------------------------------------------
  TOTAL                       :   13,747 records
======================================================================

✓ Database seeding completed successfully

======================================================================
           ✓ DATABASE INITIALIZATION COMPLETED
======================================================================
```

---

### 5. Enhanced seed_data.py main()

**Location:** `scripts/seed_data.py`

**Output:**
```
======================================================================
                 STARTING DATABASE SEEDING
======================================================================

======================================================================
                 Database State BEFORE Seeding
======================================================================
  ... (table statistics) ...
======================================================================

... (seeding with detailed logs per seeder) ...

======================================================================
                  Database State AFTER Seeding
======================================================================
  ... (table statistics) ...
======================================================================

======================================================================
                     SEEDING PERFORMANCE
======================================================================
Total time: 45.32 seconds
Speed: 303 records/second

======================================================================
          ✓ DATABASE SEEDING COMPLETED SUCCESSFULLY!
======================================================================
```

---

## Usage Examples

### Example 1: Track Specific Tables

```python
from core.db_stats import TableStatsTracker

# Track user-related tables
tracker = TableStatsTracker(db, ["users", "user_profiles", "user_roles"])

tracker.log_before("Creating test users")

# Create users
# ...

tracker.log_after("Users created", created=10)
```

### Example 2: Custom Seeder with Logging

```python
from scripts.seeders.base import BaseSeeder, SeederMetadata
from core.db_stats import log_table_change

class MySeeder(BaseSeeder):
    def seed(self):
        # Get count before
        count_before = self.db.query(MyModel).count()

        # Perform operations
        data = [...]
        created = self.batch_insert(MyModel, data)

        # Get count after
        count_after = self.db.query(MyModel).count()

        # Log the change
        log_table_change(
            "my_table",
            before_count=count_before,
            after_count=count_after,
            created=created
        )

        self.metadata.records_created = created
```

### Example 3: Log All Tables

```python
from core.db_stats import log_table_statistics

# Show all tables before operation
log_table_statistics(db, title="Initial Database State")

# Perform operations
# ...

# Show all tables after operation
log_table_statistics(db, title="Final Database State")
```

---

## Emoji Indicators

The system uses emoji indicators for better visual clarity:

| Emoji | Meaning | Usage |
|-------|---------|-------|
| 📋 | Table | Table name indicator |
| ✅ | Created | Records created |
| 🔄 | Updated | Records updated |
| ⊘ | Skipped | Records skipped |
| 📈 | Increase | Positive delta |
| 📉 | Decrease | Negative delta |
| ➡️ | No change | Zero delta |
| 📊 | Statistics | General stats |
| ⏳ | Progress | Operation in progress |
| ✓ | Success | Operation completed |
| ✗ | Failed | Operation failed |
| ⚠ | Warning | Warning message |

---

## Performance Metrics

The system tracks and displays:

### Duration
Total time taken for the operation in seconds.

```
Duration: 45.32 seconds
```

### Speed
Records processed per second.

```
Speed: 303 records/second
```

### Delta
Change in record count (before vs after).

```
Delta: +13,742 records
```

---

## Best Practices

### 1. Always Log Before and After

```python
# ✅ Good
log_table_statistics(db, title="Before Operation")
# ... perform operation ...
log_table_statistics(db, title="After Operation")

# ❌ Bad
# ... perform operation ...
log_table_statistics(db)  # Only after, no comparison
```

### 2. Use TableStatsTracker for Complex Operations

```python
# ✅ Good - automatic tracking
tracker = TableStatsTracker(db, ["table1", "table2"])
tracker.log_before()
# ... operations ...
tracker.log_after(created=10, updated=5)

# ❌ Bad - manual tracking prone to errors
before = db.query(Model).count()
# ... operations ...
after = db.query(Model).count()
print(f"Created: {after - before}")
```

### 3. Include Created/Updated/Skipped Counts

```python
# ✅ Good - detailed statistics
log_table_change(
    "users",
    before_count=5,
    after_count=10,
    created=5,
    skipped=2
)

# ❌ Bad - only delta, no context
log_table_change("users", before_count=5, after_count=10)
```

---

## Troubleshooting

### Issue: No table statistics shown

**Cause:** Database connection not established or table doesn't exist.

**Solution:**
```python
# Check if table exists
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Available tables: {tables}")
```

### Issue: Incorrect record counts

**Cause:** Counts cached, need to flush or refresh.

**Solution:**
```python
# Flush pending changes
db.flush()

# Refresh query
count = db.query(Model).count()
```

### Issue: Performance degradation with logging

**Cause:** Too many COUNT queries.

**Solution:**
```python
# Use batch operations
created = self.batch_insert(Model, data)

# Don't query count inside loops
# ❌ Bad
for item in items:
    db.add(Model(**item))
    count = db.query(Model).count()  # Expensive!

# ✅ Good
db.add_all([Model(**item) for item in items])
db.flush()
count = db.query(Model).count()  # Once after all inserts
```

---

## Summary

The enhanced logging system provides:

✅ **Complete visibility** - See exactly what's happening with your database
✅ **Performance tracking** - Monitor speed and efficiency
✅ **Easy debugging** - Quickly identify issues with detailed logs
✅ **Better UX** - Visual indicators and structured output
✅ **Production ready** - Efficient queries and minimal overhead

Use these tools to gain full insight into database operations and ensure data integrity throughout the seeding process.
