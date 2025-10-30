# Data Migration Tools

## Overview

Comprehensive data migration tools for selective export/import with transformation, rollback, and dry-run capabilities.

## Features

### 1. Selective Data Export

Export specific entities with filters and transformations.

**CLI Command:**

```bash
python cli.py export-data \
  --entities users,concepts \
  --output export.json \
  --format json \
  --date-from 2024-01-01 \
  --date-to 2025-01-01 \
  --anonymize \
  --dry-run
```

**Options:**
- `--entities` - Comma-separated entity list (users, concepts, dictionaries, languages, files, audit_logs)
- `--output` - Output file path
- `--format` - Output format (json, csv)
- `--date-from` - Filter by created date (YYYY-MM-DD)
- `--date-to` - Filter by created date (YYYY-MM-DD)
- `--anonymize` - Anonymize sensitive data (emails, passwords)
- `--dry-run` - Show what would be exported without creating file

**Example Output:**

```
================================================================================
                              Exporting Data
================================================================================

Export completed: 1500 records

Records per entity:
  users: 500
  concepts: 1000

Output file: export.json
```

### 2. Data Import with Rollback

Import data with automatic rollback snapshot creation.

**CLI Command:**

```bash
python cli.py import-data \
  --input export.json \
  --format json \
  --entities users \
  --snapshot \
  --dry-run
```

**Options:**
- `--input` - Input file path
- `--format` - Input format (json, csv)
- `--entities` - Comma-separated entity list (default: all)
- `--snapshot` - Create rollback snapshot before import (default: true)
- `--dry-run` - Validate without making changes

**Example Output:**

```
================================================================================
                              Importing Data
================================================================================

Import completed: 500 records

Records per entity:
  users: 500

Rollback snapshot: snapshot_20250127_120000
Use 'rollback-migration' command to undo this import if needed
```

### 3. Migration Snapshots

List and rollback to migration snapshots.

**List Snapshots:**

```bash
python cli.py list-snapshots
```

**Example Output:**

```
================================================================================
                            Migration Snapshots
================================================================================

Found 3 snapshots:

  snapshot_20250127_120000
    Created: 2025-01-27 12:00:00
    Records: 500
    Entities: users

  snapshot_20250126_100000
    Created: 2025-01-26 10:00:00
    Records: 1500
    Entities: users, concepts
```

**Rollback:**

```bash
python cli.py rollback-migration \
  --snapshot-id snapshot_20250127_120000 \
  --confirm
```

### 4. Data Transformation

Built-in transformation functions:

**Anonymization:**
- `anonymize_emails` - Replace emails with @example.com
- `anonymize_passwords` - Replace with default hash
- `strip_pii` - Remove personally identifiable information

**Custom Transformation:**

```python
from core.services.migration_service import MigrationService

def custom_transform(record):
    # Transform record
    record["custom_field"] = "new_value"
    return record

migration = MigrationService(db)
migration.export_data(
    entities=["users"],
    output_path="export.json",
    transform_fn=custom_transform
)
```

