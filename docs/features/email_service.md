# Email Service

Email service with **MailPit** for development testing and production SMTP support.

## Development Setup (MailPit)

**MailPit** is used for email testing in development - it catches all outgoing emails without actually sending them.

```bash
# Start services with MailPit
docker-compose -f docker-compose.dev.yml up

# Access MailPit web UI
open http://localhost:8025

# SMTP server listens on
localhost:1025
```

**MailPit features:**
- Web UI for viewing emails
- No real emails sent
- Perfect for testing email flows
- Automatic cleanup

---

## Sending Emails

### Programmatic Usage

```python
from core.email_service import email_service

# Send verification email
email_service.send_verification_email(
    to_email="user@example.com",
    username="john_doe",
    token="verification-token-123"
)

# Send password reset email
email_service.send_password_reset_email(
    to_email="user@example.com",
    username="john_doe",
    token="reset-token-456"
)

# Send custom email
email_service.send_email(
    to_email="user@example.com",
    subject="Custom Subject",
    html_content="<h1>HTML content</h1>",
    text_content="Plain text fallback"
)
```

---

## Email Templates

**Location:** `templates/emails/`

**Template engine:** Jinja2

**Available templates:**
- `verification.html` - Email verification
- `password_reset.html` - Password reset
- `email_change.html` - Email change confirmation
- `profile_change.html` - Profile change notification

**Creating new template:**
```html
<!-- templates/emails/custom.html -->
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        .button { background-color: #007bff; color: white; padding: 10px 20px; }
    </style>
</head>
<body>
    <h1>Hello {{ username }}!</h1>
    <p>{{ message }}</p>
    <a href="{{ action_url }}" class="button">Click Here</a>
</body>
</html>
```

---

## Configuration

### Development (MailPit)

```env
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=False
FROM_EMAIL=noreply@multipult.dev
```

### Production (SendGrid)

```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_sendgrid_api_key
SMTP_USE_TLS=True
FROM_EMAIL=noreply@yourdomain.com
```

### Production (AWS SES)

```env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your_aws_access_key
SMTP_PASSWORD=your_aws_secret_key
SMTP_USE_TLS=True
FROM_EMAIL=noreply@yourdomain.com
```

---

## Implementation

- **Service:** `core/email_service.py` - EmailService class
- **Templates:** `templates/emails/` - Jinja2 templates
- **Configuration:** Environment variables in `.env`

---

## Testing

```python
# In your tests
from core.email_service import email_service

def test_send_email():
    result = email_service.send_email(
        to_email="test@example.com",
        subject="Test",
        html_content="<p>Test</p>"
    )
    assert result is True
```

---

## Production Recommendations

- Use **SendGrid** or **AWS SES** for production
- Configure SPF and DKIM records for your domain
- Monitor email delivery rates
- Set up bounce and complaint handling
- Use email verification service to validate addresses
- Implement rate limiting to prevent abuse
