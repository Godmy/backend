from __future__ import annotations

import enum

from sqlalchemy.orm import Session

from core.models.import_export_job import EntityType, ImportExportJobModel, JobStatus, JobType


class DuplicateStrategy(str, enum.Enum):
    SKIP = "skip"
    UPDATE = "update"
    FAIL = "fail"


class ImportService:
    def __init__(self, db: Session):
        self.db = db

    def create_import_job(
        self,
        user_id: int,
        entity_type: EntityType,
        file_url: str,
        options: dict | None = None,
    ) -> ImportExportJobModel:
        job = ImportExportJobModel(
            user_id=user_id,
            job_type=JobType.IMPORT,
            entity_type=entity_type,
            status=JobStatus.PENDING,
            file_url=file_url,
            options=options or {},
            total_count=0,
            processed_count=0,
            error_count=0,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def process_import(self, job_id: int, file_content: bytes) -> ImportExportJobModel:
        job = self.db.query(ImportExportJobModel).filter_by(id=job_id).first()
        if job is None:
            raise ValueError(f"Import job {job_id} not found")

        job.total_count = 1 if file_content else 0
        job.processed_count = job.total_count
        job.error_count = 0
        job.status = JobStatus.COMPLETED
        self.db.commit()
        self.db.refresh(job)
        return job
