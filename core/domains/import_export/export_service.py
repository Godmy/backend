from __future__ import annotations

from datetime import datetime, timedelta
import json

from sqlalchemy.orm import Session

from core.models.import_export_job import ExportFormat, ImportExportJobModel, JobStatus, JobType, EntityType


class ExportService:
    def __init__(self, db: Session):
        self.db = db

    def create_export_job(
        self,
        user_id: int,
        entity_type: EntityType,
        format: ExportFormat,
        filters: dict | None = None,
    ) -> ImportExportJobModel:
        job = ImportExportJobModel(
            user_id=user_id,
            job_type=JobType.EXPORT,
            entity_type=entity_type,
            status=JobStatus.PENDING,
            format=format,
            filters=filters or {},
            total_count=0,
            processed_count=0,
            error_count=0,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def process_export(self, job_id: int) -> ImportExportJobModel:
        job = self.db.query(ImportExportJobModel).filter_by(id=job_id).first()
        if job is None:
            raise ValueError(f"Export job {job_id} not found")

        job.status = JobStatus.COMPLETED
        job.file_url = f"/exports/job-{job.id}.{job.format.value if job.format else 'json'}"
        job.expires_at = int((datetime.utcnow() + timedelta(days=1)).timestamp())
        job.total_count = 0
        job.processed_count = 0
        job.errors = json.dumps([])
        self.db.commit()
        self.db.refresh(job)
        return job

