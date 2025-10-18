"""
Tests for email service

Tests email sending functionality with MailPit integration
"""

import pytest
import httpx
import time
from core.email_service import email_service


class TestEmailService:
    """Test suite for EmailService"""

    @pytest.mark.asyncio
    async def test_send_simple_email(self):
        """Test sending a simple email"""
        result = email_service.send_email(
            to_email="test@example.com",
            subject="Test Email",
            html_content="<h1>Test Email</h1><p>This is a test email.</p>",
            text_content="Test Email\n\nThis is a test email."
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_send_email_to_multiple_recipients(self):
        """Test sending email to multiple recipients"""
        result = email_service.send_email(
            to_email=["user1@example.com", "user2@example.com"],
            subject="Multiple Recipients Test",
            html_content="<p>Testing multiple recipients</p>"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_send_verification_email(self):
        """Test sending verification email"""
        result = email_service.send_verification_email(
            to_email="newuser@example.com",
            username="testuser",
            token="test-verification-token-123"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_send_password_reset_email(self):
        """Test sending password reset email"""
        result = email_service.send_password_reset_email(
            to_email="user@example.com",
            username="testuser",
            token="test-reset-token-456"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_send_welcome_email(self):
        """Test sending welcome email"""
        result = email_service.send_welcome_email(
            to_email="newuser@example.com",
            username="newuser"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_render_template(self):
        """Test template rendering"""
        html = email_service.render_template(
            "verification.html",
            username="testuser",
            verification_url="http://example.com/verify?token=abc123"
        )

        assert html is not None
        assert "testuser" in html
        assert "http://example.com/verify?token=abc123" in html


@pytest.mark.integration
class TestEmailServiceWithMailPit:
    """Integration tests with MailPit API"""

    MAILPIT_API_URL = "http://mailpit:8025/api/v1"

    @pytest.mark.asyncio
    async def test_email_delivery_to_mailpit(self):
        """Test that emails are actually delivered to MailPit"""
        # Send test email
        test_subject = f"Integration Test {int(time.time())}"
        result = email_service.send_email(
            to_email="integration@example.com",
            subject=test_subject,
            html_content="<p>Integration test email</p>",
            text_content="Integration test email"
        )

        assert result is True

        # Wait a bit for email to be processed
        await self._wait_for_email()

        # Check via MailPit API
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{self.MAILPIT_API_URL}/messages")
                assert response.status_code == 200

                data = response.json()
                messages = data.get("messages", [])

                # Find our message
                found = False
                for msg in messages:
                    if msg.get("Subject") == test_subject:
                        found = True
                        assert msg["To"][0]["Address"] == "integration@example.com"
                        assert msg["From"]["Address"] == "noreply@multipult.dev"
                        break

                assert found, f"Email with subject '{test_subject}' not found in MailPit"

            except httpx.ConnectError:
                pytest.skip("MailPit is not available (not running in Docker)")

    @pytest.mark.asyncio
    async def test_verification_email_content(self):
        """Test verification email contains correct content"""
        test_subject = f"Verification Test {int(time.time())}"
        token = "test-token-abc123"

        # Send verification email
        result = email_service.send_verification_email(
            to_email="verify@example.com",
            username="verifyuser",
            token=token
        )

        assert result is True

        # Wait for email
        await self._wait_for_email()

        # Check content via MailPit API
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{self.MAILPIT_API_URL}/messages")
                assert response.status_code == 200

                data = response.json()
                messages = data.get("messages", [])

                # Find most recent message to verify@example.com
                for msg in messages:
                    if "verify@example.com" in str(msg.get("To", [])):
                        # Get full message details
                        msg_id = msg["ID"]
                        detail_response = await client.get(
                            f"{self.MAILPIT_API_URL}/message/{msg_id}"
                        )
                        detail = detail_response.json()

                        # Check content
                        html_content = detail.get("HTML", "")
                        assert "verifyuser" in html_content
                        assert token in html_content
                        assert "Подтвердите ваш email" in detail.get("Subject", "")
                        break

            except httpx.ConnectError:
                pytest.skip("MailPit is not available")

    @pytest.mark.asyncio
    async def test_password_reset_email_content(self):
        """Test password reset email contains correct content"""
        token = "reset-token-xyz789"

        # Send password reset email
        result = email_service.send_password_reset_email(
            to_email="reset@example.com",
            username="resetuser",
            token=token
        )

        assert result is True

        # Wait for email
        await self._wait_for_email()

        # Check content via MailPit API
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{self.MAILPIT_API_URL}/messages")
                assert response.status_code == 200

                data = response.json()
                messages = data.get("messages", [])

                # Find most recent message to reset@example.com
                for msg in messages:
                    if "reset@example.com" in str(msg.get("To", [])):
                        # Get full message details
                        msg_id = msg["ID"]
                        detail_response = await client.get(
                            f"{self.MAILPIT_API_URL}/message/{msg_id}"
                        )
                        detail = detail_response.json()

                        # Check content
                        html_content = detail.get("HTML", "")
                        assert "resetuser" in html_content
                        assert token in html_content
                        assert "Восстановление пароля" in detail.get("Subject", "")
                        break

            except httpx.ConnectError:
                pytest.skip("MailPit is not available")

    @staticmethod
    async def _wait_for_email(seconds: float = 1.0):
        """Wait for email to be processed by MailPit"""
        import asyncio
        await asyncio.sleep(seconds)


@pytest.mark.unit
class TestEmailServiceConfiguration:
    """Unit tests for email service configuration"""

    def test_email_service_initialization(self):
        """Test that email service initializes correctly"""
        assert email_service.smtp_host is not None
        assert email_service.smtp_port is not None
        assert email_service.from_email is not None

    def test_email_service_has_template_env(self):
        """Test that Jinja2 template environment is configured"""
        assert email_service.template_env is not None

    def test_default_configuration_values(self):
        """Test default configuration values"""
        # These should have defaults even if env vars are not set
        assert isinstance(email_service.smtp_port, int)
        assert email_service.smtp_port > 0
        assert "@" in email_service.from_email
