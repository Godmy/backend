# Email Service Documentation

## Overview

МультиПУЛЬТ использует **MailPit** для локальной разработки и тестирования email, с возможностью переключения на production SMTP (SendGrid, AWS SES, и т.д.) через переменные окружения.

## MailPit

**MailPit** — современная замена MailHog, SMTP сервер с веб-интерфейсом для разработки.

### Возможности

- ✅ Перехватывает все отправленные письма (ничего не уходит наружу)
- ✅ Веб-интерфейс для просмотра писем
- ✅ Поддержка HTML/текстовых версий
- ✅ Full-text поиск по письмам
- ✅ REST API для автоматизации тестов
- ✅ Persistence (письма сохраняются между рестартами)

### Доступ

После запуска `docker-compose -f docker-compose.dev.yml up`:

- **Web UI**: http://localhost:8025
- **SMTP Server**: localhost:1025

## Использование

### Основные методы

```python
from core.email_service import email_service

# 1. Отправка email верификации
email_service.send_verification_email(
    to_email="user@example.com",
    username="john_doe",
    token="verification-token-abc123"
)

# 2. Отправка восстановления пароля
email_service.send_password_reset_email(
    to_email="user@example.com",
    username="john_doe",
    token="reset-token-xyz789"
)

# 3. Отправка приветственного письма
email_service.send_welcome_email(
    to_email="user@example.com",
    username="john_doe"
)

# 4. Отправка кастомного email
email_service.send_email(
    to_email="user@example.com",  # Или список: ["user1@...", "user2@..."]
    subject="Тема письма",
    html_content="<h1>HTML контент</h1><p>Ваше сообщение здесь</p>",
    text_content="Текстовая версия для почтовых клиентов без HTML",
    reply_to="support@multipult.dev"  # Опционально
)
```

### Создание своих шаблонов

1. Создайте файл в `templates/emails/your_template.html`:

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Привет, {{ username }}!</h1>
        <p>{{ custom_message }}</p>
    </div>
</body>
</html>
```

2. Используйте в коде:

```python
from core.email_service import email_service

html_content = email_service.render_template(
    "your_template.html",
    username="john_doe",
    custom_message="Ваше индивидуальное сообщение"
)

email_service.send_email(
    to_email="user@example.com",
    subject="Кастомное письмо",
    html_content=html_content
)
```

## Интеграция в GraphQL

### Пример: Email верификация при регистрации

```python
# auth/schemas/auth.py
import secrets
from core.email_service import email_service

@strawberry.mutation
def register(self, info, input: UserRegistrationInput) -> AuthPayload:
    db = next(get_db())

    # Создаем пользователя
    result, error = AuthService.register_user(
        db,
        input.username,
        input.email,
        input.password
    )

    if error:
        raise Exception(error)

    # Генерируем токен верификации
    verification_token = secrets.token_urlsafe(32)

    # TODO: Сохранить токен в Redis или БД с TTL
    # redis.setex(f"verify:{verification_token}", 3600, result["user"].id)

    # Отправляем письмо
    email_service.send_verification_email(
        to_email=input.email,
        username=input.username,
        token=verification_token
    )

    return AuthPayload(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"]
    )
```

### Пример: Восстановление пароля

```python
# auth/schemas/auth.py
import secrets

@strawberry.mutation
def request_password_reset(self, email: str) -> bool:
    db = next(get_db())

    # Находим пользователя
    user = UserService.get_user_by_email(db, email)
    if not user:
        # Не раскрываем, существует ли email
        return True

    # Генерируем токен
    reset_token = secrets.token_urlsafe(32)

    # TODO: Сохранить токен в Redis с TTL 1 час
    # redis.setex(f"reset:{reset_token}", 3600, user.id)

    # Отправляем письмо
    email_service.send_password_reset_email(
        to_email=email,
        username=user.username,
        token=reset_token
    )

    return True
```

## Тестирование

### Unit тесты

```python
# tests/test_email_service.py
import pytest
from core.email_service import email_service

def test_send_email():
    result = email_service.send_email(
        to_email="test@example.com",
        subject="Test",
        html_content="<p>Test</p>"
    )
    assert result is True
```

### Интеграционные тесты с MailPit API

```python
import pytest
import httpx

@pytest.mark.integration
@pytest.mark.asyncio
async def test_email_in_mailpit():
    # Отправляем письмо
    email_service.send_email(
        to_email="integration@example.com",
        subject="Integration Test",
        html_content="<p>Test content</p>"
    )

    # Проверяем через MailPit API
    async with httpx.AsyncClient() as client:
        response = await client.get("http://mailpit:8025/api/v1/messages")
        data = response.json()

        # Проверяем, что письмо пришло
        messages = data.get("messages", [])
        assert len(messages) > 0
        assert messages[0]["To"][0]["Address"] == "integration@example.com"
```

### Запуск тестов

```bash
# Только unit тесты (быстрые)
pytest -m unit tests/test_email_service.py

# Интеграционные тесты (требуют Docker)
pytest -m integration tests/test_email_service.py

# Все тесты
pytest tests/test_email_service.py -v
```

## Production конфигурация

### SendGrid

```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_sendgrid_api_key
SMTP_USE_TLS=True
FROM_EMAIL=noreply@yourdomain.com
```

### AWS SES

```env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your_aws_access_key
SMTP_PASSWORD=your_aws_secret_key
SMTP_USE_TLS=True
FROM_EMAIL=noreply@yourdomain.com
```

### Mailgun

```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=postmaster@yourdomain.com
SMTP_PASSWORD=your_mailgun_password
SMTP_USE_TLS=True
FROM_EMAIL=noreply@yourdomain.com
```

## Troubleshooting

### Письма не отображаются в MailPit

1. Проверьте, что MailPit запущен:
   ```bash
   docker ps | grep mailpit
   ```

2. Проверьте логи:
   ```bash
   docker logs templates_mailpit
   ```

3. Проверьте переменные окружения в `docker-compose.dev.yml`:
   ```yaml
   SMTP_HOST: mailpit
   SMTP_PORT: 1025
   ```

### Ошибка подключения к SMTP

```python
# Проверьте настройки в core/email_service.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Это выведет детальные логи подключения
```

### Web UI недоступен

Убедитесь, что порт 8025 не занят:
```bash
# Windows
netstat -ano | findstr :8025

# Linux/Mac
lsof -i :8025
```

## Best Practices

### 1. Асинхронная отправка

Не блокируйте GraphQL запросы отправкой email:

```python
# ❌ Плохо - блокирует запрос
email_service.send_verification_email(...)

# ✅ Хорошо - отправка в фоне через Celery/RQ
from tasks import send_email_task
send_email_task.delay(to_email, username, token)
```

### 2. Обработка ошибок

```python
result = email_service.send_verification_email(...)
if not result:
    logger.error(f"Failed to send email to {email}")
    # Не выбрасывайте исключение - пользователь зарегистрирован
    # Можно добавить в очередь повторной отправки
```

### 3. Rate limiting

Ограничьте количество писем на email:

```python
# TODO: Добавить rate limiting через Redis
# if redis.get(f"email_limit:{email}") > 5:
#     raise Exception("Too many emails sent")
# redis.incr(f"email_limit:{email}", ex=3600)
```

### 4. Email верификация

Токены должны иметь TTL и храниться в Redis:

```python
import secrets

token = secrets.token_urlsafe(32)
redis.setex(f"verify:{token}", 3600, user_id)  # 1 час
```

### 5. Unsubscribe links

Добавьте ссылку отписки в футер:

```html
<p style="font-size: 12px; color: #999;">
    <a href="{{ unsubscribe_url }}">Отписаться от рассылки</a>
</p>
```

## Мониторинг

### Метрики

Добавьте Prometheus метрики:

```python
from prometheus_client import Counter

emails_sent = Counter('emails_sent_total', 'Total emails sent', ['type'])
emails_failed = Counter('emails_failed_total', 'Failed emails', ['type'])

# Использование
emails_sent.labels(type='verification').inc()
```

### Логирование

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "email_sent",
    to_email=to_email,
    subject=subject,
    type="verification"
)
```

## FAQ

**Q: Можно ли использовать MailPit в production?**
A: Нет, MailPit только для разработки. В production используйте SendGrid/AWS SES.

**Q: Как сохранить письма между рестартами?**
A: MailPit сохраняет письма в SQLite (`/data/mailpit.db`) через volume `mailpit_data`.

**Q: Как отправить письмо нескольким получателям?**
A: Передайте список email в `to_email`: `email_service.send_email(to_email=["a@...", "b@..."], ...)`

**Q: Поддерживаются ли вложения?**
A: Пока нет, но можно добавить через `email.mime.base.MIMEBase`.

## Полезные ссылки

- [MailPit GitHub](https://github.com/axllent/mailpit)
- [MailPit API Documentation](https://github.com/axllent/mailpit/blob/develop/docs/apiv1/README.md)
- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/)
- [Python SMTP Documentation](https://docs.python.org/3/library/smtplib.html)
