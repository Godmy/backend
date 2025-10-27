"""
File processing tasks

Background tasks for thumbnail generation and file cleanup.
"""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from celery import Task
from core.celery_app import celery_app
from core.file_storage import file_storage_service
from core.structured_logging import get_logger

logger = get_logger(__name__)


class FileTask(Task):
    """Base class for file tasks with custom error handling"""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 300  # Max 5 minutes
    retry_jitter = True


@celery_app.task(
    bind=True,
    base=FileTask,
    name="tasks.generate_thumbnail",
    queue="default",
)
def generate_thumbnail_task(
    self,
    file_path: str,
    stored_filename: str,
    request_id: Optional[str] = None,
):
    """
    Generate thumbnail for uploaded image

    Args:
        file_path: Path to the original file
        stored_filename: Stored filename for the thumbnail
        request_id: Request ID for tracing (optional)

    Returns:
        dict: Result with success status and thumbnail path

    Raises:
        Exception: If thumbnail generation fails after all retries
    """
    try:
        logger.info(
            f"Generating thumbnail for {stored_filename}",
            extra={"request_id": request_id, "task_id": self.request.id},
        )

        # Read file content
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            file_content = f.read()

        # Create thumbnail
        success, thumbnail_path = file_storage_service.create_thumbnail(
            file_content=file_content,
            stored_filename=stored_filename,
        )

        if not success:
            raise Exception("Failed to create thumbnail")

        logger.info(
            f"Thumbnail generated successfully: {thumbnail_path}",
            extra={"request_id": request_id, "task_id": self.request.id},
        )

        return {
            "success": True,
            "thumbnail_path": thumbnail_path,
            "stored_filename": stored_filename,
        }

    except Exception as exc:
        logger.error(
            f"Failed to generate thumbnail for {stored_filename}: {exc}",
            extra={
                "request_id": request_id,
                "task_id": self.request.id,
                "retry": self.request.retries,
            },
        )
        raise


@celery_app.task(
    bind=True,
    name="tasks.cleanup_old_files",
    queue="low_priority",
)
def cleanup_old_files_task(
    self,
    directory: str,
    max_age_days: int = 30,
    request_id: Optional[str] = None,
):
    """
    Clean up old files from a directory

    Args:
        directory: Directory to clean
        max_age_days: Maximum age of files to keep (default: 30 days)
        request_id: Request ID for tracing (optional)

    Returns:
        dict: Result with cleanup statistics
    """
    try:
        logger.info(
            f"Cleaning up old files in {directory} (max age: {max_age_days} days)",
            extra={"request_id": request_id, "task_id": self.request.id},
        )

        dir_path = Path(directory)
        if not dir_path.exists():
            logger.warning(f"Directory not found: {directory}")
            return {"success": False, "error": "Directory not found"}

        # Calculate cutoff time
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)

        deleted_count = 0
        deleted_size = 0
        error_count = 0

        # Iterate through files
        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                try:
                    # Check file modification time
                    mtime = file_path.stat().st_mtime
                    if mtime < cutoff_time:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        deleted_count += 1
                        deleted_size += file_size
                        logger.debug(f"Deleted old file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting file {file_path}: {e}")
                    error_count += 1

        logger.info(
            f"Cleanup complete: {deleted_count} files deleted ({deleted_size} bytes)",
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
            f"Failed to cleanup files in {directory}: {exc}",
            extra={"request_id": request_id, "task_id": self.request.id},
        )
        return {"success": False, "error": str(exc)}


@celery_app.task(
    bind=True,
    name="tasks.cleanup_temporary_files",
    queue="low_priority",
)
def cleanup_temporary_files_task(
    self,
    request_id: Optional[str] = None,
):
    """
    Clean up temporary files from common temporary directories

    Args:
        request_id: Request ID for tracing (optional)

    Returns:
        dict: Result with cleanup statistics
    """
    try:
        logger.info(
            "Cleaning up temporary files",
            extra={"request_id": request_id, "task_id": self.request.id},
        )

        # Define temporary directories to clean
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

            # Clean files older than 1 day
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
            f"Temporary cleanup complete: {total_deleted} files deleted",
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
            f"Failed to cleanup temporary files: {exc}",
            extra={"request_id": request_id, "task_id": self.request.id},
        )
        return {"success": False, "error": str(exc)}
