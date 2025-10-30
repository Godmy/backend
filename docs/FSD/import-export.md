# Import/Export System

Comprehensive data import/export system supporting JSON, CSV, and XLSX formats.

## Features

- Export/import concepts, dictionaries, users, and languages
- Multiple formats: JSON, CSV, XLSX
- Filtering and validation
- Duplicate handling strategies (skip, update, fail)
- Validation-only mode (dry run)
- Automatic cleanup of old exports (24 hours)
- Job status tracking

## GraphQL API

- **Queries:** [docs/graphql/query/import_export.md](../graphql/query/import_export.md)
- **Mutations:** [docs/graphql/mutation/import_export.md](../graphql/mutation/import_export.md)

## Supported Entities

### Concepts
- Hierarchical path structure
- Depth level tracking
- Parent-child relationships
- Soft delete support

### Dictionaries (Translations)
- Multiple language support
- Name and description fields
- Linked to concepts
- Language validation

### Users
- User profile data
- Role assignments
- Password handling (hashed)
- Email validation

### Languages
- ISO code validation
- Name and native name
- Active/inactive status
- Unique constraint handling

## Export Formats

### JSON
```json
{
  "concepts": [
    {
      "id": 1,
      "path": "/root/parent/child",
      "depth": 2,
      "created_at": "2025-01-01T00:00:00",
      "dictionaries": [
        {
          "language_id": 1,
          "name": "Child",
          "description": "Description"
        }
      ]
    }
  ]
}
```

### CSV
```csv
id,path,depth,created_at
1,/root/parent/child,2,2025-01-01T00:00:00
```

### XLSX
Excel format with:
- Formatted headers
- Auto-sized columns
- Data validation
- Multiple sheets for related data

## Import Options

### Duplicate Handling

#### Skip
- Ignores duplicate records
- Continues with next record
- No modifications to existing data
- Best for initial imports

#### Update
- Updates existing records with new data
- Matches by unique identifier
- Preserves related data
- Best for data synchronization

#### Fail
- Stops import on first duplicate
- Rollback all changes
- Returns detailed error
- Best for strict data validation

### Validation Mode

Dry run mode that:
- Validates all data without saving
- Checks for duplicates and conflicts
- Returns validation errors
- No database modifications
- Best for testing imports

## Implementation

- `core/models/import_export_job.py` - Job tracking model
- `core/services/export_service.py` - Export logic (JSON, CSV, XLSX)
- `core/services/import_service.py` - Import logic with validation
- `core/schemas/import_export.py` - GraphQL API
- `app.py` - `/exports/{filename}` endpoint for downloading files

## Job Status Tracking

### Job States
- `pending` - Job queued but not started
- `processing` - Currently processing
- `completed` - Successfully finished
- `failed` - Encountered errors

### Job Information
- Total record count
- Processed record count
- Error count
- Progress percentage
- Error details (if any)
- Start and end timestamps

## Usage Examples

### Export Concepts

```python
from core.services.export_service import ExportService

export_service = ExportService(db)

# Export as JSON
job = export_service.export_concepts(
    format="json",
    filters={"language": "en"}
)

# Download URL
url = f"/exports/{job.filename}"
```

### Import Concepts

```python
from core.services.import_service import ImportService

import_service = ImportService(db)

# Import from JSON
job = import_service.import_concepts(
    file_data=file_content,
    options={
        "on_duplicate": "update",
        "validate_only": False
    }
)

# Check status
status = import_service.get_job_status(job.id)
print(f"Progress: {status.progress_percent}%")
```

## Validation Rules

### Concepts
- Path must be unique
- Path format: `/parent/child`
- Depth calculated from path
- Parent must exist (if not root)

### Dictionaries
- Language ID must exist
- Concept ID must exist
- Name is required
- Unique per concept+language

### Users
- Email must be unique and valid
- Username must be unique
- Password must meet complexity requirements
- Role names must exist

### Languages
- ISO code must be unique
- ISO code format validation (e.g., 'en', 'ru')
- Name is required

## Error Handling

### Import Errors
- Line number in file
- Error type (validation, duplicate, missing)
- Error message
- Field name (if applicable)

### Export Errors
- Database connection issues
- Disk space errors
- Permission errors
- Format conversion errors

## Performance Considerations

### Large Exports
- Streaming for large datasets
- Chunked processing
- Progress tracking
- Memory-efficient formats (CSV)

### Large Imports
- Batch processing (1000 records)
- Transaction management
- Progress updates
- Error collection without stopping

## Cleanup

### Automatic Cleanup
- Runs daily via scheduled task
- Removes files older than 24 hours
- Removes orphaned job records
- Configurable retention period

### Manual Cleanup
```python
from core.services.export_service import ExportService

export_service = ExportService(db)
export_service.cleanup_old_exports(hours=24)
```

## Security

### Access Control
- Requires authentication
- Export/import permissions checked
- User can only export their accessible data
- Admin can export/import all data

### File Security
- Secure filename generation
- Path traversal prevention
- MIME type validation
- Virus scanning (optional)

## Configuration

```env
# .env
EXPORT_DIR=exports
EXPORT_RETENTION_HOURS=24
MAX_EXPORT_SIZE_MB=100
MAX_IMPORT_SIZE_MB=50
```

## Best Practices

1. **Always validate first** - Use validation mode before actual import
2. **Backup before import** - Create database backup before large imports
3. **Use appropriate duplicate handling** - Choose based on use case
4. **Monitor job progress** - Check status regularly for long operations
5. **Clean up exports** - Don't accumulate large export files
6. **Test with sample data** - Validate export/import with small dataset first
7. **Document custom fields** - Add comments for custom mappings
8. **Version control exports** - Track export configurations in git

## Troubleshooting

### Import fails with validation errors
- Check data format matches expected schema
- Verify all required fields are present
- Check for invalid foreign key references
- Review unique constraint violations

### Export file is empty
- Verify filters match existing data
- Check user permissions for data access
- Review soft delete status of records
- Check database connection

### Job stuck in processing
- Check background task queue
- Review application logs for errors
- Restart background workers if needed
- Check database locks

### Out of disk space
- Clean up old exports
- Reduce export size with filters
- Configure automatic cleanup
- Monitor disk usage alerts

## Full Documentation

See [docs/IMPORT_EXPORT.md](../IMPORT_EXPORT.md) for complete documentation with detailed examples and use cases.
