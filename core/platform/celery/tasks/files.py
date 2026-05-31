from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

from celery import Task

from core.platform.celery.app import celery_app
from core.platform.files.file_storage import file_storage_service
from core.platform.logging.structured_logging import get_logger


logger = get_logger(__name__)


class FileTask(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 300
    retry_jitter = True


@celery_app.task(bind=True, base=FileTask, name="tasks.generate_thumbnail", queue="default")
def generate_thumbnail_task(
    self,
    file_path: str,
    stored_filename: str,
    request_id: Optional[str] = None,
):
    try:
        logger.info(
            "Generating thumbnail for %s",
            stored_filename,
            extra={"request_id": request_id, "task_id": self.request.id},
        )

        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as file_handle:
            file_content = file_handle.read()

        success, thumbnail_path = file_storage_service.create_thumbnail(
            file_content=file_content,
            stored_filename=stored_filename,
        )
        if not success:
            raise Exception("Failed to create thumbnail")

        logger.info(
            "Thumbnail generated successfully: %s",
            thumbnail_path,
            extra={"request_id": request_id, "task_id": self.request.id},
        )
        return {
            "success": True,
            "thumbnail_path": thumbnail_path,
            "stored_filename": stored_filename,
        }
    except Exception as exc:
        logger.error(
            "Failed to generate thumbnail for %s: %s",
            stored_filename,
            exc,
            extra={
                "request_id": request_id,
                "task_id": self.request.id,
                "retry": self.request.retries,
            },
        )
        raise


@celery_app.task(bind=True, name="tasks.cleanup_old_files", queue="low_priority")
def cleanup_old_files_task(
    self,
    directory: str,
    max_age_days: int = 30,
    request_id: Optional[str] = None,
):
    try:
        logger.info(
            "Cleaning up old files in %s (max age: %s days)",
            directory,
            max_age_days,
            extra={"request_id": request_id, "task_id": self.request.id},
        )

        dir_path = Path(directory)
        if not dir_path.exists():
            logger.warning("Directory not found: %s", directory)
            return {"success": False, "error": "Directory not found"}

        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        deleted_count = 0
        deleted_size = 0
        error_count = 0

        for file_path in dir_path.rglob("*"):
            if not file_path.is_file():
                continue
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    deleted_size += file_size
            except Exception as exc:
                logger.error("Error deleting file %s: %s", file_path, exc)
                error_count += 1

        logger.info(
            "Cleanup complete: %s files deleted (%s bytes)",
            deleted_count,
            deleted_size,
            extra={
                "request_id": request_id,
                "task_id": self.request.id,
                "deleted_count": deleted_count,
                "deleted_size": deleted_size,
                "error_count": error_count,
            },
        )
        return {
            "success": True,
            "deleted_count": deleted_count,
            "deleted_size": deleted_size,
            "error_count": error_count,
        }
    except Exception as exc:
        logger.error(
            "Failed to cleanup files in %s: %s",
            directory,
            exc,
            extra={"request_id": request_id, "task_id": self.request.id},
        )
        return {"success": False, "error": str(exc)}


@celery_app.task(bind=True, name="tasks.cleanup_temporary_files", queue="low_priority")
def cleanup_temporary_files_task(
    self,
    request_id: Optional[str] = None,
):
    try:
        logger.info(
            "Cleaning up temporary files",
            extra={"request_id": request_id, "task_id": self.request.id},
        )

        temp_dirs = [
            os.getenv("TEMP_DIR", "temp"),
            os.path.join(os.getenv("UPLOAD_DIR", "uploads"), "temp"),
            os.path.join(os.getenv("EXPORT_DIR", "exports"), "temp"),
        ]

        total_deleted = 0
        total_size = 0
        total_errors = 0

        for temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                continue
            result = cleanup_old_files_task(
                directory=temp_dir,
                max_age_days=1,
                request_id=request_id,
            )
            if result.get("success"):
                total_deleted += result.get("deleted_count", 0)
                total_size += result.get("deleted_size", 0)
                total_errors += result.get("error_count", 0)

        logger.info(
            "Temporary cleanup complete: %s files deleted",
            total_deleted,
            extra={
                "request_id": request_id,
                "task_id": self.request.id,
                "total_deleted": total_deleted,
                "total_size": total_size,
            },
        )
        return {
            "success": True,
            "deleted_count": total_deleted,
            "deleted_size": total_size,
            "error_count": total_errors,
        }
    except Exception as exc:
        logger.error(
            "Failed to cleanup temporary files: %s",
            exc,
            extra={"request_id": request_id, "task_id": self.request.id},
        )
        return {"success": False, "error": str(exc)}
