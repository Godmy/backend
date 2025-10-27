"""
GraphQL schemas for data import and export jobs.
"""

import enum
from typing import List, Optional
from datetime import datetime

import strawberry
from strawberry.types import Info
from strawberry.file_uploads import Upload
from sqlalchemy.orm import Session

from core.models.import_export_job import (
    ImportExportJobModel, JobStatus, JobType, ExportFormat, EntityType
)
from core.services.export_service import ExportService
from core.services.import_service import ImportService

# ============================================================================
# Enums
# ============================================================================

@strawberry.enum(description="The current status of an import/export job.")
class JobStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@strawberry.enum(description="The file format for an export job.")
class ExportFormatEnum(str, enum.Enum):
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"

@strawberry.enum(description="The type of entity being imported or exported.")
class EntityTypeEnum(str, enum.Enum):
    CONCEPTS = "concepts"
    DICTIONARIES = "dictionaries"
    USERS = "users"
    LANGUAGES = "languages"

@strawberry.enum(description="Strategy for handling duplicate records during import.")
class DuplicateStrategyEnum(str, enum.Enum):
    SKIP = "skip"
    UPDATE = "update"
    FAIL = "fail"

# ============================================================================
# Types
# ============================================================================

@strawberry.type(description="Represents an import or export job.")
class ImportExportJobType:
    id: int
    job_type: str = strawberry.field(description="Type of job ('import' or 'export').")
    entity_type: EntityTypeEnum = strawberry.field(description="The entity being processed.")
    status: JobStatusEnum = strawberry.field(description="Current status of the job.")
    format: Optional[ExportFormatEnum] = strawberry.field(description="File format for exports.")
    file_url: Optional[str] = strawberry.field(description="Download URL for export files.")
    expires_at: Optional[datetime] = strawberry.field(description="When the export file will be deleted.")
    total_count: int = strawberry.field(description="Total number of records to process.")
    processed_count: int = strawberry.field(description="Number of records processed so far.")
    error_count: int = strawberry.field(description="Number of errors encountered.")
    errors: Optional[strawberry.scalars.JSON] = strawberry.field(description="A JSON array of error messages.")
    error_message: Optional[str] = strawberry.field(description="A general error message if the job failed.")
    progress_percent: int = strawberry.field(description="Progress percentage (0-100).")
    created_at: datetime
    updated_at: Optional[datetime]

    @staticmethod
    def from_model(job: ImportExportJobModel) -> "ImportExportJobType":
        return ImportExportJobType(
            id=job.id, job_type=job.job_type.value, entity_type=EntityTypeEnum(job.entity_type.value),
            status=JobStatusEnum(job.status.value), format=ExportFormatEnum(job.format.value) if job.format else None,
            file_url=job.file_url, expires_at=job.expires_at, total_count=job.total_count,
            processed_count=job.processed_count, error_count=job.error_count, errors=job.errors,
            error_message=job.error_message, progress_percent=job.progress_percent,
            created_at=job.created_at, updated_at=job.updated_at,
        )

@strawberry.type(description="The result of initiating an export job.")
class ExportDataPayload:
    job_id: int = strawberry.field(description="The ID of the created background job.")
    status: JobStatusEnum = strawberry.field(description="The initial status of the job.")

@strawberry.type(description="The result of initiating an import job.")
class ImportDataPayload:
    job_id: int = strawberry.field(description="The ID of the created background job.")
    status: JobStatusEnum = strawberry.field(description="The initial status of the job.")
    message: str = strawberry.field(description="A message indicating the result of the initiation.")

# ============================================================================
# Inputs
# ============================================================================

@strawberry.input(description="Filters for an export job.")
class ExportFiltersInput:
    language: Optional[str] = strawberry.field(default=None, description="Filter by language code.")
    from_date: Optional[datetime] = strawberry.field(default=None, description="Filter by creation date (from).")
    to_date: Optional[datetime] = strawberry.field(default=None, description="Filter by creation date (to).")

@strawberry.input(description="Options for an import job.")
class ImportOptionsInput:
    on_duplicate: DuplicateStrategyEnum = strawberry.field(default=DuplicateStrategyEnum.SKIP, description="How to handle duplicate records.")
    validate_only: bool = strawberry.field(default=False, description="If true, run a dry run without importing data.")

# ============================================================================
# Queries
# ============================================================================

@strawberry.type
class ImportExportQuery:
    @strawberry.field(description="""Get the status and details of a specific import/export job.

Users can only view their own jobs.

Example:
```graphql
query GetJobStatus {
  importJob(jobId: 123) {
    id
    status
    progressPercent
    errorCount
    errors
  }
}
```
""")
    def import_job(self, info: Info, job_id: int) -> Optional[ImportExportJobType]:
        user = info.context.get("user")
        if not user: raise Exception("Authentication required")
        db: Session = info.context["db"]
        job = db.query(ImportExportJobModel).filter_by(id=job_id, user_id=user.id).first()
        return ImportExportJobType.from_model(job) if job else None

    @strawberry.field(description="""Get a list of the current user's import/export jobs.

Example:
```graphql
query GetMyJobs {
  myImportExportJobs(jobType: "import", limit: 10) {
    id
    status
    entityType
    createdAt
  }
}
```
""")
    def my_import_export_jobs(
        self, info: Info, job_type: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> List[ImportExportJobType]:
        user = info.context.get("user")
        if not user: raise Exception("Authentication required")
        db: Session = info.context["db"]
        query = db.query(ImportExportJobModel).filter_by(user_id=user.id)
        if job_type: query = query.filter_by(job_type=JobType(job_type))
        jobs = query.order_by(ImportExportJobModel.created_at.desc()).offset(offset).limit(limit).all()
        return [ImportExportJobType.from_model(job) for job in jobs]

# ============================================================================
# Mutations
# ============================================================================

@strawberry.type
class ImportExportMutation:
    @strawberry.mutation(description="""Initiate a background job to export data to a file (JSON, CSV, or XLSX).

**Required permissions (for users):** `admin:read:users`

Example:
```graphql
mutation ExportConcepts {
  exportData(entityType: CONCEPTS, format: JSON, filters: { language: "en" }) {
    jobId
    status
  }
}
```
""")
    def export_data(
        self, info: Info, entity_type: EntityTypeEnum, format: ExportFormatEnum, filters: Optional[ExportFiltersInput] = None
    ) -> ExportDataPayload:
        user = info.context.get("user")
        if not user: raise Exception("Authentication required")
        db: Session = info.context["db"]
        export_service = ExportService(db)

        if entity_type == EntityTypeEnum.USERS and not getattr(user, "is_admin", False):
            raise Exception("Only admins can export users")

        job = export_service.create_export_job(
            user_id=user.id, entity_type=EntityType(entity_type.value),
            format=ExportFormat(format.value), filters=filters.__dict__ if filters else {}
        )
        # In a real async setup, this would be handled by Celery.
        # For sync execution, we process it immediately.
        export_service.process_export(job.id)
        return ExportDataPayload(job_id=job.id, status=JobStatusEnum(job.status.value))

    @strawberry.mutation(description="""Initiate a background job to import data from a file (JSON, CSV, or XLSX).

This mutation requires a multipart form-data request.

**Required permissions (for users):** `admin:create:users`

Example (using a GraphQL client):
```graphql
mutation ImportConcepts($file: Upload!) {
  importData(
    file: $file,
    entityType: CONCEPTS,
    options: { onDuplicate: UPDATE }
  ) {
    jobId
    status
    message
  }
}
```
""")
    async def import_data(
        self, info: Info, file: Upload, entity_type: EntityTypeEnum, options: Optional[ImportOptionsInput] = None
    ) -> ImportDataPayload:
        user = info.context.get("user")
        if not user: raise Exception("Authentication required")
        db: Session = info.context["db"]
        import_service = ImportService(db)

        if entity_type == EntityTypeEnum.USERS and not getattr(user, "is_admin", False):
            raise Exception("Only admins can import users")

        file_content = await file.read()
        options_dict = options.__dict__ if options else {}

        job = import_service.create_import_job(
            user_id=user.id, entity_type=EntityType(entity_type.value),
            file_url=file.filename, options=options_dict
        )
        # In a real async setup, this would be handled by Celery.
        # For sync execution, we process it immediately.
        job = import_service.process_import(job.id, file_content)

        if job.status == JobStatus.COMPLETED:
            message = f"Successfully imported {job.processed_count} records"
            if job.error_count > 0: message += f" with {job.error_count} errors."
        else:
            message = f"Import failed: {job.error_message}"

        return ImportDataPayload(job_id=job.id, status=JobStatusEnum(job.status.value), message=message)