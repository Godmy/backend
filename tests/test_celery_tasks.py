"""
Tests for Celery background tasks
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

import pytest
from celery import Celery

from tasks.email_tasks import (
    send_email_task,
    send_verification_email_task,
    send_password_reset_email_task,
    send_welcome_email_task,
)
from tasks.file_tasks import (
    generate_thumbnail_task,
    cleanup_old_files_task,
    cleanup_temporary_files_task,
)
from tasks.periodic_tasks import (
    periodic_file_cleanup_task,
    periodic_health_check_task,
)


@pytest.fixture
def celery_app():
    """Create a test Celery app"""
    app = Celery("test")
    app.conf.update(
        broker_url="memory://",
        result_backend="cache+memory://",
        task_always_eager=True,  # Execute tasks synchronously
        task_eager_propagates=True,  # Propagate exceptions
    )
    return app


class TestEmailTasks:
    """Test email sending tasks"""

    @patch("tasks.email_tasks.email_service")
    def test_send_email_task_success(self, mock_email_service):
        """Test successful email sending"""
        mock_email_service.send_email.return_value = True

        result = send_email_task(
            to_email="test@example.com",
            subject="Test Subject",
            html_content="<p>Test content</p>",
            text_content="Test content",
        )

        assert result is True
        mock_email_service.send_email.assert_called_once()

    @patch("tasks.email_tasks.email_service")
    def test_send_email_task_failure(self, mock_email_service):
        """Test email sending failure"""
        mock_email_service.send_email.return_value = False

        with pytest.raises(Exception, match="Email service returned failure"):
            send_email_task(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<p>Test content</p>",
            )

    @patch("tasks.email_tasks.email_service")
    def test_send_verification_email_task(self, mock_email_service):
        """Test verification email sending"""
        mock_email_service.send_verification_email.return_value = True

        result = send_verification_email_task(
            to_email="test@example.com",
            username="testuser",
            token="test-token-123",
        )

        assert result is True
        mock_email_service.send_verification_email.assert_called_once_with(
            to_email="test@example.com",
            username="testuser",
            token="test-token-123",
        )

    @patch("tasks.email_tasks.email_service")
    def test_send_password_reset_email_task(self, mock_email_service):
        """Test password reset email sending"""
        mock_email_service.send_password_reset_email.return_value = True

        result = send_password_reset_email_task(
            to_email="test@example.com",
            username="testuser",
            token="reset-token-456",
        )

        assert result is True
        mock_email_service.send_password_reset_email.assert_called_once()

    @patch("tasks.email_tasks.email_service")
    def test_send_welcome_email_task(self, mock_email_service):
        """Test welcome email sending"""
        mock_email_service.send_welcome_email.return_value = True

        result = send_welcome_email_task(
            to_email="test@example.com",
            username="newuser",
        )

        assert result is True
        mock_email_service.send_welcome_email.assert_called_once()


class TestFileTasks:
    """Test file processing tasks"""

    @patch("tasks.file_tasks.file_storage_service")
    def test_generate_thumbnail_task_success(self, mock_file_storage):
        """Test successful thumbnail generation"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            tmp_file.write(b"fake image data")
            tmp_file_path = tmp_file.name

        try:
            mock_file_storage.create_thumbnail.return_value = (True, "/path/to/thumbnail.jpg")

            result = generate_thumbnail_task(
                file_path=tmp_file_path,
                stored_filename="test_image.jpg",
            )

            assert result["success"] is True
            assert "thumbnail_path" in result
            assert result["stored_filename"] == "test_image.jpg"

        finally:
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def test_generate_thumbnail_task_file_not_found(self):
        """Test thumbnail generation with missing file"""
        with pytest.raises(FileNotFoundError):
            generate_thumbnail_task(
                file_path="/nonexistent/file.jpg",
                stored_filename="test.jpg",
            )

    def test_cleanup_old_files_task(self):
        """Test old file cleanup"""
        # Create a temporary directory with files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some test files
            test_file = Path(tmpdir) / "test_file.txt"
            test_file.write_text("test content")

            # Set modification time to old (this won't actually delete it in test)
            result = cleanup_old_files_task(
                directory=tmpdir,
                max_age_days=30,
            )

            assert result["success"] is True
            assert "deleted_count" in result

    def test_cleanup_old_files_task_directory_not_found(self):
        """Test cleanup with nonexistent directory"""
        result = cleanup_old_files_task(
            directory="/nonexistent/directory",
            max_age_days=30,
        )

        assert result["success"] is False
        assert "error" in result

    def test_cleanup_temporary_files_task(self):
        """Test temporary file cleanup"""
        result = cleanup_temporary_files_task()

        # Should return success even if directories don't exist
        assert result["success"] is True
        assert "deleted_count" in result


class TestPeriodicTasks:
    """Test periodic scheduled tasks"""

    @patch("tasks.periodic_tasks.cleanup_temporary_files_task")
    @patch("tasks.periodic_tasks.cleanup_old_files_task")
    def test_periodic_file_cleanup_task(self, mock_cleanup_old, mock_cleanup_temp):
        """Test periodic file cleanup"""
        mock_cleanup_temp.return_value = {
            "success": True,
            "deleted_count": 5,
            "deleted_size": 1024,
        }
        mock_cleanup_old.return_value = {
            "success": True,
            "deleted_count": 10,
            "deleted_size": 2048,
        }

        result = periodic_file_cleanup_task()

        assert "temp_cleanup" in result
        assert "old_files_cleanup" in result
        mock_cleanup_temp.assert_called_once()

    @patch("tasks.periodic_tasks.engine")
    @patch("tasks.periodic_tasks.redis_client")
    def test_periodic_health_check_task(self, mock_redis, mock_engine):
        """Test periodic health check"""
        # Mock successful database connection
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock successful Redis ping
        mock_redis.ping.return_value = True

        result = periodic_health_check_task()

        assert result["success"] is True
        assert result["healthy"] is True
        assert "checks" in result
        assert result["checks"]["database"] is True
        assert result["checks"]["redis"] is True
        assert result["checks"]["celery"] is True


class TestCeleryConfiguration:
    """Test Celery app configuration"""

    def test_celery_app_configuration(self):
        """Test that Celery app is properly configured"""
        from core.celery_app import celery_app

        # Check broker URL is set
        assert celery_app.conf.broker_url is not None

        # Check task serialization
        assert celery_app.conf.task_serializer == "json"
        assert "json" in celery_app.conf.accept_content

        # Check task acknowledgment settings
        assert celery_app.conf.task_acks_late is True
        assert celery_app.conf.task_track_started is True

        # Check queues are configured
        assert celery_app.conf.task_queues is not None

    def test_celery_beat_schedule(self):
        """Test that Celery Beat schedule is configured"""
        from core.celery_app import celery_app

        # Check beat schedule exists
        assert celery_app.conf.beat_schedule is not None

    def test_task_registration(self):
        """Test that tasks are registered"""
        from core.celery_app import celery_app

        # Check that email tasks are registered
        assert "tasks.send_email" in celery_app.tasks
        assert "tasks.send_verification_email" in celery_app.tasks
        assert "tasks.send_password_reset_email" in celery_app.tasks
        assert "tasks.send_welcome_email" in celery_app.tasks

        # Check that file tasks are registered
        assert "tasks.generate_thumbnail" in celery_app.tasks
        assert "tasks.cleanup_old_files" in celery_app.tasks
        assert "tasks.cleanup_temporary_files" in celery_app.tasks

        # Check that periodic tasks are registered
        assert "tasks.periodic_file_cleanup" in celery_app.tasks
        assert "tasks.periodic_health_check" in celery_app.tasks


class TestCeleryHealthCheck:
    """Test Celery health check in health service"""

    @patch("core.services.health_service.celery_app")
    def test_celery_health_check_healthy(self, mock_celery_app):
        """Test Celery health check when workers are running"""
        from core.services.health_service import HealthCheckService

        # Mock inspect results
        mock_inspect = MagicMock()
        mock_inspect.stats.return_value = {"worker1": {"pool": "prefork"}}
        mock_inspect.active.return_value = {"worker1": []}
        mock_inspect.registered.return_value = {"worker1": ["task1"]}
        mock_celery_app.control.inspect.return_value = mock_inspect

        result = HealthCheckService.check_celery()

        assert result["status"] == "healthy"
        assert result["workers_count"] == 1

    @patch("core.services.health_service.celery_app")
    def test_celery_health_check_no_workers(self, mock_celery_app):
        """Test Celery health check when no workers are running"""
        from core.services.health_service import HealthCheckService

        # Mock inspect returns None when no workers
        mock_inspect = MagicMock()
        mock_inspect.stats.return_value = None
        mock_celery_app.control.inspect.return_value = mock_inspect

        result = HealthCheckService.check_celery()

        assert result["status"] == "unhealthy"
        assert result["workers_count"] == 0


class TestTaskRetryLogic:
    """Test task retry and backoff configuration"""

    def test_email_task_retry_configuration(self):
        """Test email task retry settings"""
        # EmailTask base class should have retry configured
        assert send_email_task.autoretry_for == (Exception,)
        assert send_email_task.retry_backoff is True
        assert send_email_task.retry_jitter is True

    def test_file_task_retry_configuration(self):
        """Test file task retry settings"""
        assert generate_thumbnail_task.autoretry_for == (Exception,)
        assert generate_thumbnail_task.retry_backoff is True
