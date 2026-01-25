# Email Verification & Password Reset Flow

Полное руководство по реализации email верификации и восстановления пароля в МультиПУЛЬТ.

## 📋 Содержание

- [Обзор](#обзор)
- [Архитектура](#архитектура)
- [Сценарии использования](#сценарии-использования)
- [GraphQL API](#graphql-api)
- [Тестирование](#тестирование)
- [Безопасность](#безопасность)

---

## Обзор

Система реализует два основных сценария:

1. **Email Verification** - подтверждение email при регистрации
2. **Password Reset** - восстановление пароля через email

### Технологии

- **Redis** - хранение временных токенов с TTL
- **MailPit** - тестирование email (development)
- **SendGrid/AWS SES** - отправка email (production)
- **GraphQL** - API для взаимодействия

---

## Архитектура

### Компоненты

```
┌─────────────────┐
│   GraphQL API   │  ← Мутации для регистрации, верификации, сброса
└────────┬────────┘
         │
┌────────▼────────┐
│  Token Service  │  ← Создание и проверка токенов
└────────┬────────┘
         │
┌────────▼────────┐
│   Redis         │  ← Хранение токенов (TTL: 1-24 часа)
└─────────────────┘

┌─────────────────┐
│  Email Service  │  ← Отправка писем через SMTP
└────────┬────────┘
         │
┌────────▼────────┐
│   MailPit       │  ← Development
│   SendGrid      │  ← Production
└─────────────────┘
```

### Хранение Токенов

Токены хранятся в Redis с префиксами:

- `verify:{token}` → `user_id` (TTL: 24 часа)
- `reset:{token}` → `user_id` (TTL: 1 час)
- `rate:email:{email}` → `count` (TTL: 1 час)

---

## Сценарии использования

### 1. Регистрация с Email Верификацией

```
┌─────────┐       ┌─────────┐       ┌────────┐       ┌───────┐
│ Клиент  │       │ GraphQL │       │ Redis  │       │ Email │
└────┬────┘       └────┬────┘       └───┬────┘       └───┬───┘
     │                 │                 │                │
     │ 1. register()   │                 │                │
     ├────────────────►│                 │                │
     │                 │ 2. create_token │                │
     │                 ├────────────────►│                │
     │                 │                 │                │
     │                 │ 3. send_email   │                │
     │                 ├─────────────────┼───────────────►│
     │                 │                 │                │
     │ 4. AuthPayload  │                 │                │
     │◄────────────────┤                 │                │
     │                 │                 │                │
     │ 5. verify_email(token)            │                │
     ├────────────────►│                 │                │
     │                 │ 6. verify_token │                │
     │                 ├────────────────►│                │
     │                 │ 7. user_id      │                │
     │                 │◄────────────────┤                │
     │                 │ 8. update DB    │                │
     │                 │    (verified)   │                │
     │                 │                 │                │
     │ 9. Success      │                 │                │
     │◄────────────────┤                 │                │
```

#### Шаг 1: Регистрация

```graphql
mutation Register {
  register(input: {
    username: "john_doe"
    email: "john@example.com"
    password: "SecurePass123!"
    firstName: "John"
    lastName: "Doe"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

**Что происходит:**
1. Создается пользователь с `is_verified: false`
2. Генерируется токен верификации (32 байта, URL-safe)
3. Токен сохраняется в Redis: `verify:{token}` → `user_id` (TTL: 24ч)
4. Отправляется email с ссылкой: `{FRONTEND_URL}/verify-email?token={token}`
5. Возвращается JWT для немедленного использования

#### Шаг 2: Верификация Email

```graphql
mutation VerifyEmail {
  verifyEmail(input: {
    token: "токен_из_email"
  }) {
    success
    message
  }
}
```

**Что происходит:**
1. Проверяется токен в Redis
2. Получается `user_id`
3. Обновляется `user.is_verified = true`
4. Токен удаляется из Redis (одноразовый)

#### Шаг 3: Повторная отправка (опционально)

```graphql
mutation ResendVerification {
  resendVerificationEmail(email: "john@example.com") {
    success
    message
  }
}
```

**Rate limiting:** Максимум 3 запроса в час на email.

---

### 2. Восстановление Пароля

```
┌─────────┐       ┌─────────┐       ┌────────┐       ┌───────┐
│ Клиент  │       │ GraphQL │       │ Redis  │       │ Email │
└────┬────┘       └────┬────┘       └───┬────┘       └───┬───┘
     │                 │                 │                │
     │ 1. request_password_reset()       │                │
     ├────────────────►│                 │                │
     │                 │ 2. create_token │                │
     │                 ├────────────────►│                │
     │                 │                 │                │
     │                 │ 3. send_email   │                │
     │                 ├─────────────────┼───────────────►│
     │                 │                 │                │
     │ 4. Success      │                 │                │
     │◄────────────────┤                 │                │
     │                 │                 │                │
     │ 5. reset_password(token, new_pass)│                │
     ├────────────────►│                 │                │
     │                 │ 6. verify_token │                │
     │                 ├────────────────►│                │
     │                 │ 7. user_id      │                │
     │                 │◄────────────────┤                │
     │                 │ 8. update pass  │                │
     │                 │    hash in DB   │                │
     │                 │ 9. invalidate   │                │
     │                 │    all tokens   │                │
     │                 ├────────────────►│                │
     │                 │                 │                │
     │ 10. Success     │                 │                │
     │◄────────────────┤                 │                │
```

#### Шаг 1: Запрос Сброса

```graphql
mutation RequestPasswordReset {
  requestPasswordReset(input: {
    email: "john@example.com"
  }) {
    success
    message
  }
}
```

**Что происходит:**
1. Проверяется rate limit (3 запроса/час)
2. Ищется пользователь по email (не раскрываем существование!)
3. Генерируется токен сброса
4. Токен сохраняется: `reset:{token}` → `user_id` (TTL: 1ч)
5. Отправляется email с ссылкой
6. Всегда возвращается успех (безопасность)

#### Шаг 2: Сброс Пароля

```graphql
mutation ResetPassword {
  resetPassword(input: {
    token: "токен_из_email"
    newPassword: "NewSecurePass456!"
  }) {
    success
    message
  }
}
```

**Что происходит:**
1. Проверяется токен в Redis
2. Получается `user_id`
3. Валидируется новый пароль (≥8 символов)
4. Хешируется и сохраняется новый пароль
5. Удаляются ВСЕ токены пользователя (verify + reset)
6. Токен сброса удаляется

---

## GraphQL API

### Mutations

#### 1. Register
```graphql
mutation {
  register(input: {
    username: String!
    email: String!
    password: String!
    firstName: String
    lastName: String
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

#### 2. Verify Email
```graphql
mutation {
  verifyEmail(input: {
    token: String!
  }) {
    success
    message
  }
}
```

#### 3. Resend Verification
```graphql
mutation {
  resendVerificationEmail(
    email: String!
  ) {
    success
    message
  }
}
```

#### 4. Request Password Reset
```graphql
mutation {
  requestPasswordReset(input: {
    email: String!
  }) {
    success
    message
  }
}
```

#### 5. Reset Password
```graphql
mutation {
  resetPassword(input: {
    token: String!
    newPassword: String!
  }) {
    success
    message
  }
}
```

### Примеры Ответов

**Успех:**
```json
{
  "data": {
    "verifyEmail": {
      "success": true,
      "message": "Email verified successfully"
    }
  }
}
```

**Ошибка:**
```json
{
  "data": {
    "verifyEmail": {
      "success": false,
      "message": "Invalid or expired verification token"
    }
  }
}
```

---

## Тестирование

### Unit Tests

```bash
# Тесты токен-сервиса
pytest tests/test_email_verification.py::TestTokenService -v

# Тесты Redis клиента
pytest tests/test_email_verification.py::TestRedisClient -v
```

### Integration Tests

```bash
# Полный flow верификации
pytest tests/test_email_verification.py::TestEmailVerificationFlow -v
```

### Manual Testing

1. **Запустите сервисы:**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

2. **Откройте GraphQL Playground:**
```
http://localhost:8000/graphql
```

3. **Зарегистрируйтесь:**
```graphql
mutation {
  register(input: {
    username: "testuser"
    email: "test@example.com"
    password: "Test123!"
  }) {
    accessToken
    refreshToken
  }
}
```

4. **Проверьте MailPit:**
```
http://localhost:8025
```

5. **Скопируйте токен из письма и верифицируйте:**
```graphql
mutation {
  verifyEmail(input: {
    token: "YOUR_TOKEN_HERE"
  }) {
    success
    message
  }
}
```

---

## Безопасность

### Реализованные Меры

#### 1. Rate Limiting
- **3 запроса в час** на email
- Предотвращает спам и атаки
- Хранится в Redis: `rate:email:{email}`

#### 2. Одноразовые Токены
- Токен удаляется после использования
- Предотвращает повторное использование

#### 3. TTL для Токенов
- **Verification:** 24 часа
- **Reset:** 1 час
- Автоматическое удаление из Redis

#### 4. Не Раскрывать Email
```python
if not user:
    return MessageResponse(
        success=True,
        message="If this email is registered, you will receive a link"
    )
```

#### 5. Инвалидация Токенов
При сбросе пароля удаляются:
- Все токены верификации
- Все токены сброса
- (TODO: JWT refresh tokens)

#### 6. Валидация Пароля
```python
if len(password) < 8:
    return error("Password must be at least 8 characters")
```

### Рекомендации Production

#### 1. HTTPS Only
```python
# В production используйте HTTPS
FRONTEND_URL=https://yourdomain.com
```

#### 2. Strong Passwords
Добавьте валидацию:
- Минимум 12 символов
- Заглавные и строчные буквы
- Цифры и спецсимволы
- Проверка на common passwords

#### 3. Email Verification Required
```python
# Запретить login без верификации
if not user.is_verified:
    raise Exception("Please verify your email first")
```

#### 4. 2FA (Optional)
Добавьте двухфакторную аутентификацию:
- TOTP (Google Authenticator)
- SMS codes
- Backup codes

#### 5. Audit Logs
Логируйте:
- Попытки верификации
- Попытки сброса пароля
- Успешные сбросы

#### 6. Redis Persistence
```yaml
# docker-compose.yml
redis:
  command: redis-server --appendonly yes
  volumes:
    - redis_data:/data
```

---

## Troubleshooting

### Проблема: Email не приходит

**Проверка:**
```bash
# 1. Проверьте MailPit
open http://localhost:8025

# 2. Проверьте логи приложения
docker logs templates_app_dev

# 3. Проверьте переменные окружения
docker exec templates_app_dev env | grep SMTP
```

**Решение:**
- Убедитесь, что MailPit запущен
- Проверьте `SMTP_HOST=mailpit`
- Проверьте `SMTP_PORT=1025`

### Проблема: Токен недействителен

**Проверка:**
```bash
# Проверьте Redis
docker exec templates_redis redis-cli
> KEYS verify:*
> TTL verify:{token}
```

**Причины:**
- Токен истек (проверьте TTL)
- Токен уже использован (одноразовый)
- Redis перезапустился (без persistence)

### Проблема: Rate limit блокирует

**Проверка:**
```bash
docker exec templates_redis redis-cli
> KEYS rate:email:*
> GET rate:email:test@example.com
> TTL rate:email:test@example.com
```

**Решение:**
```bash
# Сбросить rate limit для email
docker exec templates_redis redis-cli DEL rate:email:test@example.com
```

---

## Monitoring & Metrics

### Метрики для Prometheus

```python
# TODO: Добавить метрики
from prometheus_client import Counter, Histogram

emails_sent = Counter('emails_sent_total', 'Total emails sent', ['type'])
email_failures = Counter('email_failures_total', 'Failed emails', ['type'])
token_verifications = Counter('token_verifications_total', 'Token verifications', ['type', 'status'])

# Использование
emails_sent.labels(type='verification').inc()
token_verifications.labels(type='verification', status='success').inc()
```

### Логирование

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "email_verification_attempt",
    user_id=user_id,
    email=email,
    token_ttl=ttl,
    success=True
)
```

---

## Next Steps

- [ ] Добавить валидацию сильных паролей
- [ ] Реализовать JWT blacklist для refresh tokens
- [ ] Добавить 2FA (TOTP)
- [ ] Email notification при смене пароля
- [ ] Логирование всех попыток аутентификации
- [ ] Admin панель для управления токенами
- [ ] Метрики и мониторинг

---

## Полезные Ссылки

- [Документация Email Service](EMAIL_SERVICE.md)
- [MailPit Quick Start](MAILPIT_QUICKSTART.md)
- [OWASP Password Guidelines](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)

---

**Готово!** Теперь у вас полностью рабочая система email верификации и восстановления пароля. 🎉
