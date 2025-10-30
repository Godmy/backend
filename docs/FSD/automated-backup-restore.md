# Automated Backup & Restore

## Overview

Comprehensive automated backup system with S3 support, retention policy, and verification.

## Features

#### 1. Advanced Backup Creation

Create compressed backups with S3 upload support.

**CLI Command:**

```bash
python cli.py backup-advanced \
  --output backup.sql.gz \
  --compress \
  --upload-s3
```

**Options:**
- `--output` - Output file path (default: auto-generated)
- `--compress/--no-compress` - Compress with gzip (default: true)
- `--upload-s3/--no-upload-s3` - Upload to S3 if configured (default: false)

**Example Output:**

```
================================================================================
                       Creating Advanced Backup
================================================================================

Backup created: backup_20250127_120000.sql.gz
  Size: 45.23 MB
  Compressed: Yes
  Checksum: 1a2b3c4d5e6f7890...
  S3 Key: backups/backup_20250127_120000.sql.gz
```

#### 2. Backup Listing

List all available backups (local and S3).

**CLI Command:**

```bash
python cli.py list-backups
```

**Example Output:**

```
================================================================================
                           Available Backups
================================================================================

Found 10 backups:

  backup_20250127_120000.sql.gz
    Created: 2025-01-27 12:00:00
    Size: 45.23 MB
    Type: full
    S3: backups/backup_20250127_120000.sql.gz

  backup_20250126_020000.sql.gz
    Created: 2025-01-26 02:00:00
    Size: 44.12 MB
    Type: full
```

#### 3. Backup Retention Policy

Apply retention policy automatically or manually.

**CLI Command:**

```bash
python cli.py apply-retention \
  --daily 7 \
  --weekly 4 \
  --monthly 12 \
  --dry-run
```

**Options:**
- `--daily` - Keep last N daily backups (default: 7)
- `--weekly` - Keep last N weekly backups (default: 4)
- `--monthly` - Keep last N monthly backups (default: 12)
- `--dry-run` - Show what would be deleted

**Example Output:**

```
================================================================================
                     Applying Backup Retention Policy
================================================================================

Retention policy: 7 daily, 4 weekly, 12 monthly
Kept: 23 backups
Deleted: 5 backups

Deleted backups:
  - backup_20241115_020000.sql.gz
  - backup_20241108_020000.sql.gz
  - backup_20241101_020000.sql.gz
```

#### 4. Automated Daily Backups

Celery tasks run automated daily backups.

**Start Celery Worker:**

```bash
celery -A core.celery_app worker --loglevel=info
```

**Start Celery Beat Scheduler:**

```bash
celery -A core.celery_app beat --loglevel=info
```

**Schedule:**
- Daily backups: 2:00 AM UTC
- Weekly retention: 3:00 AM UTC on Sundays

**Manual Trigger:**

```python
from core.tasks import create_automated_backup

# Trigger backup task
result = create_automated_backup.delay(compress=True, upload_to_s3=True)
```

#### 5. S3 Configuration

Configure S3-compatible storage for backups.

**Environment Variables:**

```bash
# S3 Configuration
S3_BACKUP_BUCKET=my-backups
S3_ENDPOINT_URL=https://s3.amazonaws.com  # Optional for MinIO
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1

# Backup Directory
BACKUP_DIR=backups/  # Local backup directory
```

**Supported Storage:**
- AWS S3
- MinIO
- DigitalOcean Spaces
- Any S3-compatible storage

