"""
Email service that renders local templates and delegates delivery to state-machine.

The state-machine owns routing to concrete HTTP gateways:
gateway-email-brevo, gateway-email-resend, and future providers.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Optional, Union

import httpx
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"


class EmailService:
    def __init__(self):
        self.from_email = os.getenv("FROM_EMAIL", "noreply@vibe-management.pro")
        self.from_name = os.getenv("FROM_NAME", "Vibe Management")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        self.state_machine_url = os.getenv("STATE_MACHINE_URL", "http://state-machine:8000/graphql")
        self.provider_order = [
            provider.strip()
            for provider in os.getenv("EMAIL_PROVIDER_ORDER", "brevo,resend").split(",")
            if provider.strip()
        ]

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
        recipients = self._recipients(to_email)
        for provider in self.provider_order:
            try:
                if self._send_via_state_machine(
                    provider=provider,
                    recipients=recipients,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    reply_to=reply_to,
                    idempotency_key=idempotency_key,
                ):
                    return True
            except Exception as exc:
                logger.warning("Email provider %s failed for %s: %s", provider, to_email, exc)

        logger.error("Failed to send email to %s through providers %s", to_email, self.provider_order)
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

    def _send_via_state_machine(
        self,
        provider: str,
        recipients: list[dict[str, Optional[str]]],
        subject: str,
        html_content: str,
        text_content: Optional[str],
        reply_to: Optional[str],
        idempotency_key: Optional[str],
    ) -> bool:
        query = """
        mutation SendEmail($inputTo: [EmailRecipientInput!]!, $subject: String!, $provider: String!, $htmlContent: String, $textContent: String, $fromEmail: String, $fromName: String, $replyTo: String, $idempotencyKey: String) {
          sendEmail(to: $inputTo, subject: $subject, provider: $provider, htmlContent: $htmlContent, textContent: $textContent, fromEmail: $fromEmail, fromName: $fromName, replyTo: $replyTo, idempotencyKey: $idempotencyKey) {
            id
            status
            currentState
            context
          }
        }
        """
        variables = {
            "inputTo": recipients,
            "subject": subject,
            "provider": provider,
            "htmlContent": html_content,
            "textContent": text_content,
            "fromEmail": self.from_email,
            "fromName": self.from_name,
            "replyTo": reply_to,
            "idempotencyKey": idempotency_key,
        }

        with httpx.Client(timeout=65.0) as client:
            response = client.post(self.state_machine_url, json={"query": query, "variables": variables})
            response.raise_for_status()

        data = response.json()
        if data.get("errors"):
            raise RuntimeError(data["errors"])

        task = data.get("data", {}).get("sendEmail") or {}
        return task.get("status") == "COMPLETED" and task.get("currentState") == "COMPLETED"

    @staticmethod
    def _recipients(to_email: Union[str, List[str]]) -> list[dict[str, Optional[str]]]:
        emails = [to_email] if isinstance(to_email, str) else to_email
        return [{"email": email, "name": None} for email in emails]


email_service = EmailService()
