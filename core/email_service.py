"""
Email service for sending emails via SMTP

Supports multiple backends:
- Development: MailPit (SMTP without auth)
- Production: SendGrid/AWS SES/any SMTP with auth
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional, Union

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for sending transactional emails

    Features:
    - Template rendering with Jinja2
    - HTML and plain text versions
    - Development/Production SMTP support
    - Error handling and logging
    """

    def __init__(self):
        """Initialize email service with configuration from environment"""
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "1025"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@multipult.dev")
        self.use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

        # Setup Jinja2 template environment
        templates_path = Path(__file__).parent.parent / "templates" / "emails"
        templates_path.mkdir(parents=True, exist_ok=True)

        self.template_env = Environment(
            loader=FileSystemLoader(str(templates_path)),
            autoescape=select_autoescape(["html", "xml"]),
        )

        logger.info(
            f"EmailService initialized: {self.smtp_host}:{self.smtp_port} " f"(TLS: {self.use_tls})"
        )

    def send_email(
        self,
        to_email: Union[str, List[str]],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """
        Send an email

        Args:
            to_email: Recipient email address or list of addresses
            subject: Email subject
            html_content: HTML version of the email
            text_content: Plain text version (optional, will use html if not provided)
            reply_to: Reply-To email address (optional)

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email

            # Handle multiple recipients
            if isinstance(to_email, list):
                msg["To"] = ", ".join(to_email)
                recipients = to_email
            else:
                msg["To"] = to_email
                recipients = [to_email]

            if reply_to:
                msg["Reply-To"] = reply_to

            # Add plain text version
            if text_content:
                part1 = MIMEText(text_content, "plain", "utf-8")
                msg.attach(part1)

            # Add HTML version
            part2 = MIMEText(html_content, "html", "utf-8")
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                # Enable TLS if configured
                if self.use_tls:
                    server.starttls()

                # Login if credentials provided
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)

                # Send message
                server.send_message(msg)

            logger.info(f"Email sent successfully to {recipients}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
            return False

    def render_template(self, template_name: str, **context) -> str:
        """
        Render email template with context

        Args:
            template_name: Name of template file (e.g., 'verification.html')
            **context: Template variables

        Returns:
            Rendered HTML string
        """
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise

    def send_verification_email(self, to_email: str, username: str, token: str) -> bool:
        """
        Send email verification link

        Args:
            to_email: Recipient email
            username: User's username
            token: Verification token

        Returns:
            True if sent successfully
        """
        verification_url = f"{self.frontend_url}/verify-email?token={token}"

        try:
            html_content = self.render_template(
                "verification.html", username=username, verification_url=verification_url
            )

            text_content = f"""
Здравствуйте, {username}!

Спасибо за регистрацию в МультиПУЛЬТ!

Пожалуйста, подтвердите ваш email, перейдя по ссылке:
{verification_url}

Если вы не регистрировались на нашем сайте, проигнорируйте это письмо.

--
Команда МультиПУЛЬТ
            """.strip()

            return self.send_email(
                to_email=to_email,
                subject="Подтвердите ваш email - МультиПУЛЬТ",
                html_content=html_content,
                text_content=text_content,
            )
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            return False

    def send_password_reset_email(self, to_email: str, username: str, token: str) -> bool:
        """
        Send password reset link

        Args:
            to_email: Recipient email
            username: User's username
            token: Password reset token

        Returns:
            True if sent successfully
        """
        reset_url = f"{self.frontend_url}/reset-password?token={token}"

        try:
            html_content = self.render_template(
                "password_reset.html", username=username, reset_url=reset_url
            )

            text_content = f"""
Здравствуйте, {username}!

Вы запросили сброс пароля для вашей учетной записи в МультиПУЛЬТ.

Перейдите по ссылке для создания нового пароля:
{reset_url}

Ссылка действительна в течение 1 часа.

Если вы не запрашивали сброс пароля, проигнорируйте это письмо.

--
Команда МультиПУЛЬТ
            """.strip()

            return self.send_email(
                to_email=to_email,
                subject="Восстановление пароля - МультиПУЛЬТ",
                html_content=html_content,
                text_content=text_content,
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            return False

    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """
        Send welcome email to new user

        Args:
            to_email: Recipient email
            username: User's username

        Returns:
            True if sent successfully
        """
        try:
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #4CAF50; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Добро пожаловать в МультиПУЛЬТ!</h1>
        <p>Здравствуйте, <strong>{username}</strong>!</p>
        <p>Мы рады приветствовать вас в нашей системе управления шаблонами и контентом.</p>
        <p>Теперь вы можете:</p>
        <ul>
            <li>Создавать и управлять концепциями</li>
            <li>Работать с многоязычными словарями</li>
            <li>Организовывать контент в иерархическую структуру</li>
        </ul>
        <p>Если у вас есть вопросы, не стесняйтесь обращаться к нашей поддержке.</p>
        <div class="footer">
            <p>С уважением,<br>Команда МультиПУЛЬТ</p>
        </div>
    </div>
</body>
</html>
            """.strip()

            text_content = f"""
Добро пожаловать в МультиПУЛЬТ!

Здравствуйте, {username}!

Мы рады приветствовать вас в нашей системе управления шаблонами и контентом.

Теперь вы можете:
- Создавать и управлять концепциями
- Работать с многоязычными словарями
- Организовывать контент в иерархическую структуру

Если у вас есть вопросы, не стесняйтесь обращаться к нашей поддержке.

--
С уважением,
Команда МультиПУЛЬТ
            """.strip()

            return self.send_email(
                to_email=to_email,
                subject="Добро пожаловать в МультиПУЛЬТ!",
                html_content=html_content,
                text_content=text_content,
            )
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            return False


# Singleton instance
email_service = EmailService()
