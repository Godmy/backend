"""
Celery Tasks for Background Jobs

Provides background tasks for automated operations like backups.

Implementation for User Story #27 - Automated Database Backup & Restore

Tasks:
    - create_automated_backup: Create daily database backup
    - apply_backup_retention: Apply retention policy
    - verify_backup: Verify backup integrity
"""

import logging
from datetime import datetime
from celery import Task

from core.celery_app import app
from core.services.backup_service import BackupService
from core.structured_logging import get_logger

logger = get_logger(__name__)


class DatabaseTask(Task):
    """Base task with database session management."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(
            f"Task {self.name} failed",
            extra={
                "task_id": task_id,
                "error": str(exc),
                "args": args,
                "kwargs": kwargs
            },
            exc_info=True
        )


@app.task(base=DatabaseTask, bind=True, name="core.tasks.create_automated_backup")
def create_automated_backup(self, compress: bool = True, upload_to_s3: bool = True):
    """
    Create automated database backup.

    Args:
        compress: Compress backup with gzip (default: True)
        upload_to_s3: Upload to S3 if configured (default: True)

    Returns:
        Backup metadata dictionary
    """
    logger.info("Starting automated backup task")

    try:
        backup_service = BackupService()

        # Create backup
        metadata = backup_service.create_backup(
            output_path=None,  # Auto-generate filename
            compress=compress,
            upload_to_s3=upload_to_s3,
            backup_type="full"
        )

        logger.info(
            "Automated backup completed",
            extra={
                "filename": metadata.filename,
                "size_bytes": metadata.size_bytes,
                "s3_key": metadata.s3_key
            }
        )

        return {
            "filename": metadata.filename,
            "size_bytes": metadata.size_bytes,
            "compressed": metadata.compressed,
            "s3_key": metadata.s3_key,
            "created_at": metadata.created_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Automated backup failed: {e}", exc_info=True)
        raise


@app.task(base=DatabaseTask, bind=True, name="core.tasks.apply_backup_retention")
def apply_backup_retention(
    self,
    daily: int = 7,
    weekly: int = 4,
    monthly: int = 12
):
    """
    Apply backup retention policy.

    Args:
        daily: Keep last N daily backups (default: 7)
        weekly: Keep last N weekly backups (default: 4)
        monthly: Keep last N monthly backups (default: 12)

    Returns:
        Retention result dictionary
    """
    logger.info(
        "Starting backup retention task",
        extra={"daily": daily, "weekly": weekly, "monthly": monthly}
    )

    try:
        backup_service = BackupService()

        # Apply retention policy
        result = backup_service.apply_retention_policy(
            daily=daily,
            weekly=weekly,
            monthly=monthly,
            dry_run=False
        )

        logger.info(
            "Backup retention applied",
            extra={
                "kept": len(result["kept"]),
                "deleted": len(result["deleted"])
            }
        )

        return result

    except Exception as e:
        logger.error(f"Backup retention failed: {e}", exc_info=True)
        raise


@app.task(base=DatabaseTask, bind=True, name="core.tasks.verify_backup")
def verify_backup(self, backup_path: str):
    """
    Verify backup integrity.

    Args:
        backup_path: Path to backup file

    Returns:
        Verification result (bool)
    """
    logger.info(f"Starting backup verification: {backup_path}")

    try:
        backup_service = BackupService()

        # Verify backup
        result = backup_service.verify_backup(backup_path)

        logger.info(f"Backup verification completed: {result}")

        return result

    except Exception as e:
        logger.error(f"Backup verification failed: {e}", exc_info=True)
        raise


@app.task(bind=True, name="core.tasks.test_task")
def test_task(self):
    """Test task to verify Celery is working."""
    logger.info("Test task executed successfully")
    return {"status": "success", "timestamp": datetime.now().isoformat()}
