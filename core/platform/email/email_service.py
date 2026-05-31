"""
Email service supporting SMTP (MailPit for dev) and Resend (production).

Set RESEND_API_KEY to route all outgoing mail through Resend.
Without it, mail is sent via SMTP — the default points at MailPit.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional, Union

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"


class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "mailpit")
        self.smtp_port = int(os.getenv("SMTP_PORT", "1025"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.use_tls = os.getenv("SMTP_USE_TLS", "False").lower() == "true"
        self.from_email = os.getenv("FROM_EMAIL", "noreply@vibe-management.pro")
        self.from_name = os.getenv("FROM_NAME", "Vibe Management")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

        self._resend_api_key = os.getenv("RESEND_API_KEY", "")

        self.template_env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=True,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def render_template(self, template_name: str, **kwargs) -> str:
        template = self.template_env.get_template(template_name)
        return template.render(**kwargs)

    def send_email(
        self,
        to_email: Union[str, List[str]],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        reply_to: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> bool:
        try:
            if self._resend_api_key:
                return self._send_via_resend(
                    to_email, subject, html_content, text_content, reply_to, idempotency_key
                )
            return self._send_via_smtp(to_email, subject, html_content, text_content, reply_to)
        except Exception as exc:
            logger.error("Failed to send email to %s: %s", to_email, exc)
            return False

    def send_verification_email(
        self,
        to_email: str,
        username: str,
        token: str,
        idempotency_key: Optional[str] = None,
    ) -> bool:
        url = f"{self.frontend_url}/verify-email?token={token}"
        html = self.render_template("verification.html", username=username, verification_url=url)
        return self.send_email(
            to_email=to_email,
            subject="Подтвердите ваш email",
            html_content=html,
            text_content=f"Привет, {username}!\n\nПодтвердите email: {url}",
            idempotency_key=idempotency_key,
        )

    def send_password_reset_email(
        self,
        to_email: str,
        username: str,
        token: str,
        idempotency_key: Optional[str] = None,
    ) -> bool:
        url = f"{self.frontend_url}/reset-password?token={token}"
        html = self.render_template("password_reset.html", username=username, reset_url=url)
        return self.send_email(
            to_email=to_email,
            subject="Восстановление пароля",
            html_content=html,
            text_content=f"Привет, {username}!\n\nСброс пароля: {url}",
            idempotency_key=idempotency_key,
        )

    def send_welcome_email(
        self,
        to_email: str,
        username: str,
        idempotency_key: Optional[str] = None,
    ) -> bool:
        html = (
            f'<div style="font-family:sans-serif;max-width:600px;margin:0 auto">'
            f"<h1>Добро пожаловать, {username}!</h1>"
            f"<p>Ваш аккаунт успешно создан. Добро пожаловать!</p>"
            f"</div>"
        )
        return self.send_email(
            to_email=to_email,
            subject="Добро пожаловать в Vibe Management!",
            html_content=html,
            text_content=f"Добро пожаловать, {username}!\n\nВаш аккаунт успешно создан.",
            idempotency_key=idempotency_key,
        )

    # ------------------------------------------------------------------
    # Internal senders
    # ------------------------------------------------------------------

    def _send_via_resend(
        self,
        to_email: Union[str, List[str]],
        subject: str,
        html_content: str,
        text_content: Optional[str],
        reply_to: Optional[str],
        idempotency_key: Optional[str] = None,
    ) -> bool:
        import resend as resend_sdk  # optional dep — only needed in production

        resend_sdk.api_key = self._resend_api_key

        recipients = [to_email] if isinstance(to_email, str) else to_email
        from_address = f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email

        params: resend_sdk.Emails.SendParams = {
            "from": from_address,
            "to": recipients,
            "subject": subject,
            "html": html_content,
        }
        if text_content:
            params["text"] = text_content
        if reply_to:
            params["reply_to"] = [reply_to]

        if idempotency_key:
            result = resend_sdk.Emails.send(params, idempotency_key=idempotency_key)
        else:
            result = resend_sdk.Emails.send(params)

        logger.info("Resend message id: %s", result.get("id"))
        return bool(result.get("id"))

    def _send_via_smtp(
        self,
        to_email: Union[str, List[str]],
        subject: str,
        html_content: str,
        text_content: Optional[str],
        reply_to: Optional[str],
    ) -> bool:
        recipients = [to_email] if isinstance(to_email, str) else to_email

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = ", ".join(recipients)
        if reply_to:
            msg["Reply-To"] = reply_to

        if text_content:
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.use_tls:
                server.starttls()
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            server.sendmail(self.from_email, recipients, msg.as_string())

        logger.info("SMTP email sent to %s via %s:%s", recipients, self.smtp_host, self.smtp_port)
        return True


email_service = EmailService()
