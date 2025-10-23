# Import/Export Queries

**Required:** Authorization header

## Check Import Job Status

Get status and progress of an import job.

```graphql
query ImportJobStatus {
  importJob(jobId: 123) {
    id
    status
    entityType
    totalCount
    processedCount
    errorCount
    errors
    progressPercent
    createdAt
    completedAt
  }
}
```

**Job status values:**
- `pending` - Job queued, not started yet
- `in_progress` - Currently processing
- `completed` - Successfully finished
- `failed` - Failed with errors
- `cancelled` - Manually cancelled

**Response fields:**
- `totalCount` - Total number of records to process
- `processedCount` - Number of records processed so far
- `errorCount` - Number of errors encountered
- `errors` - Array of error messages (max 100)
- `progressPercent` - Progress percentage (0-100)

---

## List My Import/Export Jobs

Get list of your import/export jobs.

```graphql
query MyJobs {
  myJobs(limit: 20, offset: 0) {
    id
    jobType
    status
    entityType
    format
    totalCount
    processedCount
    errorCount
    progressPercent
    createdAt
    completedAt
  }
}
```

**Filter options:**
- `jobType` - Filter by IMPORT or EXPORT
- `limit` - Max results per page
- `offset` - Pagination offset

---

## Implementation

- `core/models/import_export_job.py` - ImportExportJobModel
- `core/schemas/import_export.py` - GraphQL API
- `core/services/import_service.py` - Import logic
- `core/services/export_service.py` - Export logic

**Automatic cleanup:**
- Export files deleted after 24 hours
- Completed jobs archived after 30 days
