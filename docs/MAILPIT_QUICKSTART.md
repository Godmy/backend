# MailPit Quick Start Guide

## 🚀 Быстрый старт

### 1. Запустите сервисы с MailPit

```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 2. Откройте MailPit Web UI

Перейдите в браузере: **http://localhost:8025**

### 3. Протестируйте отправку email

```bash
python scripts/test_email.py
```

### 4. Проверьте письма в MailPit UI

Все отправленные письма появятся в интерфейсе MailPit.

## 📧 Примеры использования

### Отправка верификации email

```python
from core.email_service import email_service

email_service.send_verification_email(
    to_email="user@example.com",
    username="john_doe",
    token="verification-token-abc123"
)
```

### Отправка восстановления пароля

```python
email_service.send_password_reset_email(
    to_email="user@example.com",
    username="john_doe",
    token="reset-token-xyz789"
)
```

### Отправка кастомного письма

```python
email_service.send_email(
    to_email="user@example.com",
    subject="Привет!",
    html_content="<h1>Привет!</h1><p>Это тестовое письмо.</p>",
    text_content="Привет!\n\nЭто тестовое письмо."
)
```

## 🧪 Тестирование

### Unit тесты (быстрые)

```bash
pytest -m unit tests/test_email_service.py
```

### Integration тесты (с MailPit)

```bash
pytest -m integration tests/test_email_service.py
```

### Все тесты

```bash
pytest tests/test_email_service.py -v
```

## 🔍 MailPit Features

### Web UI

- **Просмотр всех писем**: список всех перехваченных писем
- **HTML/Text версии**: переключение между версиями
- **Поиск**: полнотекстовый поиск по письмам
- **Attachments**: просмотр вложений (если есть)
- **Raw view**: просмотр исходного кода письма
- **Headers**: просмотр заголовков письма

### API Endpoints

```bash
# Получить список писем
curl http://localhost:8025/api/v1/messages

# Получить конкретное письмо
curl http://localhost:8025/api/v1/message/{id}

# Удалить все письма
curl -X DELETE http://localhost:8025/api/v1/messages

# Поиск писем
curl "http://localhost:8025/api/v1/search?query=test"
```

## ⚙️ Конфигурация

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

## 🐛 Troubleshooting

### Письма не появляются в MailPit

1. Проверьте, что MailPit запущен:
   ```bash
   docker ps | grep mailpit
   ```

2. Проверьте логи MailPit:
   ```bash
   docker logs templates_mailpit
   ```

3. Проверьте логи приложения:
   ```bash
   docker logs templates_app_dev
   ```

### Web UI недоступен

Убедитесь, что порт 8025 не занят другим процессом.

### Ошибка подключения к SMTP

Проверьте переменные окружения в `docker-compose.dev.yml`:
```yaml
environment:
  SMTP_HOST: mailpit
  SMTP_PORT: 1025
```

## 📚 Дополнительная информация

- [Полная документация Email Service](EMAIL_SERVICE.md)
- [MailPit GitHub](https://github.com/axllent/mailpit)
- [MailPit API Docs](https://github.com/axllent/mailpit/blob/develop/docs/apiv1/README.md)

## 🎯 Next Steps

1. ✅ MailPit настроен и работает
2. ⏭️ Добавьте токены верификации в Redis (TTL)
3. ⏭️ Реализуйте GraphQL мутации для верификации
4. ⏭️ Добавьте GraphQL мутации для восстановления пароля
5. ⏭️ Настройте production SMTP (SendGrid/AWS SES)
6. ⏭️ Добавьте rate limiting для email
7. ⏭️ Настройте мониторинг отправки email

## 🌟 Pro Tips

1. **Persistence**: Письма сохраняются между рестартами в volume `mailpit_data`

2. **Search**: Используйте full-text поиск в UI для быстрого поиска писем

3. **API Testing**: Используйте MailPit API в интеграционных тестах:
   ```python
   async with httpx.AsyncClient() as client:
       response = await client.get("http://mailpit:8025/api/v1/messages")
       messages = response.json()["messages"]
   ```

4. **Clear emails**: Очистите все письма перед тестами:
   ```bash
   curl -X DELETE http://localhost:8025/api/v1/messages
   ```

5. **Multiple environments**: Используйте разные FROM_EMAIL для dev/staging/prod
