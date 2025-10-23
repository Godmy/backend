# Import/Export Mutations

**Required:** Authorization header

## Export Data

Export data to JSON, CSV, or XLSX format.

```graphql
mutation ExportConcepts {
  exportData(
    entityType: CONCEPTS
    format: JSON
    filters: { language: "en" }
  ) {
    jobId
    url
    expiresAt
    status
  }
}
```

**Entity types:**
- `CONCEPTS` - Export concepts
- `DICTIONARIES` - Export translations
- `USERS` - Export users (admin only)
- `LANGUAGES` - Export languages

**Formats:**
- `JSON` - JSON format (best for re-import)
- `CSV` - CSV format (good for Excel)
- `XLSX` - Excel format (includes formatting)

**Filter options:**
- `language` - Filter by language code
- `fromDate`, `toDate` - Date range filter
- `conceptPath` - Filter by concept path prefix

**Response:**
- `jobId` - Job ID for tracking status
- `url` - Download URL (available when complete)
- `expiresAt` - When file will be deleted (24 hours)
- `status` - Job status (pending, in_progress, completed)

**Download file:**
```
GET /exports/{filename}
```

---

## Import Data

Import data from JSON, CSV, or XLSX file.

```graphql
mutation ImportConcepts($file: Upload!) {
  importData(
    file: $file
    entityType: CONCEPTS
    options: {
      onDuplicate: UPDATE
      validateOnly: false
    }
  ) {
    jobId
    status
    message
  }
}
```

**Entity types:**
- `CONCEPTS` - Import concepts
- `DICTIONARIES` - Import translations
- `USERS` - Import users (admin only)
- `LANGUAGES` - Import languages

**Import options:**
- `onDuplicate` - What to do with duplicates:
  - `SKIP` - Skip duplicate records
  - `UPDATE` - Update existing records
  - `FAIL` - Fail on duplicate
- `validateOnly` - Dry run mode (validate without importing)

**Validation:**
- File format validation
- Schema validation
- Duplicate detection
- Foreign key validation

**Response:**
- `jobId` - Job ID for tracking progress
- `status` - Initial job status
- `message` - Success or error message

---

## Check Import Status

Use the `importJob` query to track progress:

```graphql
query CheckProgress {
  importJob(jobId: 123) {
    status
    processedCount
    totalCount
    errorCount
    errors
    progressPercent
  }
}
```

---

## Example Workflow

**Export:**
```graphql
# 1. Start export
mutation {
  exportData(entityType: CONCEPTS, format: JSON) {
    jobId
    url
  }
}

# 2. Download file from URL
# curl http://localhost:8000/exports/concepts_20250116.json
```

**Import:**
```graphql
# 1. Upload file
mutation ImportFile($file: Upload!) {
  importData(
    file: $file
    entityType: CONCEPTS
    options: { onDuplicate: UPDATE }
  ) {
    jobId
  }
}

# 2. Check progress
query {
  importJob(jobId: 456) {
    status
    progressPercent
    errorCount
  }
}
```

---

## Supported Formats

**JSON:**
```json
[
  {
    "id": 1,
    "path": "colors",
    "depth": 0,
    "parent_id": null
  }
]
```

**CSV:**
```csv
id,path,depth,parent_id
1,colors,0,
2,colors.red,1,1
```

**XLSX:**
- Excel spreadsheet with headers
- Multiple sheets for related data
- Includes formatting and validation

---

## Implementation

- `core/models/import_export_job.py` - Job tracking
- `core/services/export_service.py` - Export logic (JSON, CSV, XLSX)
- `core/services/import_service.py` - Import logic with validation
- `core/schemas/import_export.py` - GraphQL API
- `app.py` - `/exports/{filename}` endpoint

**See full documentation:** [docs/IMPORT_EXPORT.md](../../IMPORT_EXPORT.md)
