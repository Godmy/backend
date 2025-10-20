"""
GraphQL схемы для импорта/экспорта
"""

from typing import List, Optional
from datetime import datetime

import strawberry
from strawberry.types import Info
from strawberry.file_uploads import Upload

from core.models.import_export_job import (
    ImportExportJobModel,
    JobStatus,
    JobType,
    ExportFormat,
    EntityType,
)
from core.services.export_service import ExportService
from core.services.import_service import ImportService
from auth.dependencies.permissions import IsAuthenticated, IsAdmin


# Strawberry Enums
@strawberry.enum
class JobStatusEnum(str):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@strawberry.enum
class ExportFormatEnum(str):
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"


@strawberry.enum
class EntityTypeEnum(str):
    CONCEPTS = "concepts"
    DICTIONARIES = "dictionaries"
    USERS = "users"
    LANGUAGES = "languages"


@strawberry.enum
class DuplicateStrategyEnum(str):
    SKIP = "skip"
    UPDATE = "update"
    FAIL = "fail"


# Types
@strawberry.type
class ImportExportJobType:
    id: int
    job_type: str
    entity_type: EntityTypeEnum
    status: JobStatusEnum
    format: Optional[ExportFormatEnum]
    file_url: Optional[str]
    expires_at: Optional[int]
    total_count: int
    processed_count: int
    error_count: int
    errors: Optional[str]  # JSON string
    error_message: Optional[str]
    progress_percent: int
    created_at: datetime
    updated_at: Optional[datetime]

    @staticmethod
    def from_model(job: ImportExportJobModel) -> "ImportExportJobType":
        import json

        return ImportExportJobType(
            id=job.id,
            job_type=job.job_type.value,
            entity_type=EntityTypeEnum(job.entity_type.value),
            status=JobStatusEnum(job.status.value),
            format=ExportFormatEnum(job.format.value) if job.format else None,
            file_url=job.file_url,
            expires_at=job.expires_at,
            total_count=job.total_count,
            processed_count=job.processed_count,
            error_count=job.error_count,
            errors=json.dumps(job.errors) if job.errors else None,
            error_message=job.error_message,
            progress_percent=job.progress_percent,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )


@strawberry.type
class ExportDataPayload:
    job_id: int
    url: Optional[str]
    expires_at: Optional[int]
    status: JobStatusEnum


@strawberry.type
class ImportDataPayload:
    job_id: int
    status: JobStatusEnum
    message: str


@strawberry.type
class ImportJobStatusPayload:
    job: ImportExportJobType
    progress: int
    status: JobStatusEnum
    processed_count: int
    error_count: int
    errors: Optional[List[str]]


# Inputs
@strawberry.input
class ExportFiltersInput:
    language: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


@strawberry.input
class ImportOptionsInput:
    on_duplicate: DuplicateStrategyEnum = DuplicateStrategyEnum.SKIP
    validate_only: bool = False


# Query
@strawberry.type
class ImportExportQuery:
    @strawberry.field(permission_classes=[IsAuthenticated])
    def import_job(self, info: Info, job_id: int) -> Optional[ImportExportJobType]:
        """Получить статус задания импорта/экспорта"""
        db = info.context["db"]
        user = info.context.get("user")

        job = db.query(ImportExportJobModel).filter_by(id=job_id).first()

        # Проверяем права доступа
        if job and (job.user_id == user.id or user.is_admin):
            return ImportExportJobType.from_model(job)

        return None

    @strawberry.field(permission_classes=[IsAuthenticated])
    def my_import_export_jobs(
        self,
        info: Info,
        job_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ImportExportJobType]:
        """Получить мои задания импорта/экспорта"""
        db = info.context["db"]
        user = info.context.get("user")

        query = db.query(ImportExportJobModel).filter_by(user_id=user.id)

        if job_type:
            query = query.filter_by(job_type=JobType(job_type))

        jobs = query.order_by(ImportExportJobModel.created_at.desc()).offset(offset).limit(
            limit
        ).all()

        return [ImportExportJobType.from_model(job) for job in jobs]


# Mutations
@strawberry.type
class ImportExportMutation:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def export_data(
        self,
        info: Info,
        entity_type: EntityTypeEnum,
        format: ExportFormatEnum,
        filters: Optional[ExportFiltersInput] = None,
    ) -> ExportDataPayload:
        """Экспортировать данные"""
        db = info.context["db"]
        user = info.context.get("user")

        export_service = ExportService(db)

        # Проверяем права (users могут экспортировать только admin)
        if entity_type == EntityTypeEnum.USERS and not user.is_admin:
            raise Exception("Only admins can export users")

        # Создаем задание
        filters_dict = {}
        if filters:
            if filters.language:
                filters_dict["language"] = filters.language
            if filters.date_from:
                filters_dict["date_from"] = filters.date_from
            if filters.date_to:
                filters_dict["date_to"] = filters.date_to

        job = export_service.create_export_job(
            user_id=user.id,
            entity_type=EntityType(entity_type.value),
            format=ExportFormat(format.value),
            filters=filters_dict,
        )

        # Обрабатываем синхронно (для async версии нужен Celery)
        try:
            job = export_service.process_export(job.id)
            return ExportDataPayload(
                job_id=job.id,
                url=job.file_url,
                expires_at=job.expires_at,
                status=JobStatusEnum(job.status.value),
            )
        except Exception as e:
            return ExportDataPayload(
                job_id=job.id,
                url=None,
                expires_at=None,
                status=JobStatusEnum.FAILED,
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def import_data(
        self,
        info: Info,
        file: Upload,
        entity_type: EntityTypeEnum,
        options: Optional[ImportOptionsInput] = None,
    ) -> ImportDataPayload:
        """Импортировать данные"""
        db = info.context["db"]
        user = info.context.get("user")

        import_service = ImportService(db)

        # Проверяем права (users могут импортировать только admin)
        if entity_type == EntityTypeEnum.USERS and not user.is_admin:
            raise Exception("Only admins can import users")

        # Читаем файл
        file_content = await file.read()
        filename = file.filename

        # Создаем задание
        options_dict = {}
        if options:
            options_dict["onDuplicate"] = options.on_duplicate.value
            options_dict["validateOnly"] = options.validate_only

        job = import_service.create_import_job(
            user_id=user.id,
            entity_type=EntityType(entity_type.value),
            file_url=filename,
            options=options_dict,
        )

        # Обрабатываем синхронно
        try:
            job = import_service.process_import(job.id, file_content)

            if job.status == JobStatus.COMPLETED:
                message = f"Successfully imported {job.processed_count} records"
                if job.error_count > 0:
                    message += f" ({job.error_count} errors)"
            else:
                message = f"Import failed: {job.error_message}"

            return ImportDataPayload(
                job_id=job.id,
                status=JobStatusEnum(job.status.value),
                message=message,
            )
        except Exception as e:
            return ImportDataPayload(
                job_id=job.id,
                status=JobStatusEnum.FAILED,
                message=str(e),
            )
