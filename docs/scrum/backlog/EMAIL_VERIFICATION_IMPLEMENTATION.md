# Email Verification & Password Reset Implementation

## ✅ Что реализовано

### 1. Redis для хранения токенов
- ✅ Redis контейнер в `docker-compose.dev.yml`
- ✅ Redis client (`core/redis_client.py`)
- ✅ Persistence через volume `redis_data`
- ✅ Health checks

### 2. Token Service
- ✅ Генерация безопасных токенов (32 байта, URL-safe)
- ✅ Verification tokens (TTL: 24 часа)
- ✅ Reset tokens (TTL: 1 час)
- ✅ Rate limiting (3 запроса/час на email)
- ✅ Одноразовые токены (удаляются после использования)

### 3. GraphQL Mutations
- ✅ `register` - регистрация с автоматической отправкой email верификации
- ✅ `verifyEmail` - подтверждение email по токену
- ✅ `resendVerificationEmail` - повторная отправка письма верификации
- ✅ `requestPasswordReset` - запрос сброса пароля
- ✅ `resetPassword` - сброс пароля по токену

### 4. Тестирование
- ✅ Unit тесты для TokenService
- ✅ Integration тесты для email flow
- ✅ Redis client тесты

### 5. Документация
- ✅ Полная документация flow (`docs/EMAIL_VERIFICATION_FLOW.md`)
- ✅ Обновлен `.env.example`

---

## 🚀 Быстрый старт

### Шаг 1: Запустите сервисы

```bash
docker-compose -f docker-compose.dev.yml up -d
```

Проверьте, что все контейнеры запущены:
```bash
docker ps
```

Должны быть:
- `templates_db_dev` (PostgreSQL)
- `templates_redis` (Redis)
- `templates_mailpit` (MailPit)
- `templates_app_dev` (Application)

### Шаг 2: Откройте интерфейсы

- **GraphQL Playground**: http://localhost:8000/graphql
- **MailPit UI**: http://localhost:8025
- **Redis CLI**: `docker exec -it templates_redis redis-cli`

### Шаг 3: Тестируйте сценарий

#### 3.1 Регистрация

```graphql
mutation Register {
  register(input: {
    username: "testuser"
    email: "test@example.com"
    password: "SecurePass123!"
    firstName: "Test"
    lastName: "User"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

**Результат:**
- Пользователь создан с `is_verified: false`
- JWT токены возвращены (можно сразу использовать)
- Email верификации отправлен в MailPit

#### 3.2 Проверьте Email

Откройте http://localhost:8025 и найдите письмо верификации.

Скопируйте токен из ссылки:
```
http://localhost:5173/verify-email?token=XXXXXXXXXXXXX
```

#### 3.3 Верифицируйте Email

```graphql
mutation VerifyEmail {
  verifyEmail(input: {
    token: "ВСТАВЬТЕ_ТОК ЕН_СЮДА"
  }) {
    success
    message
  }
}
```

**Ожидаемый ответ:**
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

#### 3.4 Тест сброса пароля

```graphql
mutation RequestReset {
  requestPasswordReset(input: {
    email: "test@example.com"
  }) {
    success
    message
  }
}
```

Проверьте MailPit, скопируйте токен:

```graphql
mutation ResetPassword {
  resetPassword(input: {
    token: "ВСТАВЬТЕ_ТОКЕН_СЮДА"
    newPassword: "NewSecurePass456!"
  }) {
    success
    message
  }
}
```

---

## 📊 Структура файлов

```
backend/
├── core/
│   ├── redis_client.py              ✅ Redis connection
│   └── email_service.py             ✅ Email sending
├── auth/
│   ├── services/
│   │   ├── token_service.py         ✅ Token management
│   │   ├── user_service.py          ✅ Updated with get_by_email
│   │   └── auth_service.py          (Existing)
│   └── schemas/
│       └── auth.py                  ✅ All mutations implemented
├── tests/
│   └── test_email_verification.py   ✅ Complete test suite
├── docs/
│   └── EMAIL_VERIFICATION_FLOW.md   ✅ Full documentation
├── docker-compose.dev.yml           ✅ Redis added
├── requirements.txt                 ✅ redis package added
└── .env.example                     ✅ Redis config added
```

---

## 🔑 Ключевые API Endpoints

### 1. Регистрация (с автоматической отправкой email)

```graphql
mutation {
  register(input: {
    username: "john_doe"
    email: "john@example.com"
    password: "SecurePass123!"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

### 2. Верификация Email

```graphql
mutation {
  verifyEmail(input: {
    token: "токен_из_email"
  }) {
    success
    message
  }
}
```

### 3. Повторная отправка верификации

```graphql
mutation {
  resendVerificationEmail(email: "john@example.com") {
    success
    message
  }
}
```

### 4. Запрос сброса пароля

```graphql
mutation {
  requestPasswordReset(input: {
    email: "john@example.com"
  }) {
    success
    message
  }
}
```

### 5. Сброс пароля

```graphql
mutation {
  resetPassword(input: {
    token: "токен_из_email"
    newPassword: "NewPass123!"
  }) {
    success
    message
  }
}
```

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты email verification
pytest tests/test_email_verification.py -v

# Только unit тесты
pytest tests/test_email_verification.py::TestTokenService -v

# Только integration тесты
pytest tests/test_email_verification.py::TestEmailVerificationFlow -v
```

### Проверка Redis

```bash
# Подключиться к Redis CLI
docker exec -it templates_redis redis-cli

# Посмотреть все ключи
KEYS *

# Посмотреть токены верификации
KEYS verify:*

# Посмотреть токены сброса
KEYS reset:*

# Проверить TTL
TTL verify:XXXXXXXXX

# Посмотреть значение
GET verify:XXXXXXXXX
```

---

## 🔒 Безопасность

### Реализованные меры

✅ **Rate Limiting**
- 3 запроса в час на email
- Хранится в Redis с TTL 1 час

✅ **Одноразовые токены**
- Удаляются после использования
- Невозможно повторное использование

✅ **TTL для токенов**
- Verification: 24 часа
- Reset: 1 час
- Автоматическое удаление

✅ **Не раскрывать существование email**
- Всегда возвращается успех
- Не указывается, существует ли email

✅ **Инвалидация всех токенов при сбросе пароля**

### Рекомендации для Production

1. **Усилить валидацию паролей**
```python
# TODO: Добавить в UserService
- Минимум 12 символов
- Заглавные и строчные буквы
- Цифры и спецсимволы
- Проверка на common passwords
```

2. **Требовать верификацию для login**
```python
# В AuthService.login_user
if not user.is_verified:
    return None, "Please verify your email first"
```

3. **Использовать HTTPS**
```env
FRONTEND_URL=https://yourdomain.com
```

4. **Настроить production SMTP**
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USE_TLS=True
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_api_key
```

---

## 📝 Примеры использования

### Пример фронтенда (React)

```typescript
// Registration
const register = async () => {
  const result = await graphqlClient.mutate({
    mutation: REGISTER_MUTATION,
    variables: {
      input: {
        username: 'john_doe',
        email: 'john@example.com',
        password: 'SecurePass123!'
      }
    }
  });

  // Save tokens
  localStorage.setItem('accessToken', result.data.register.accessToken);

  // Show message
  alert('Registration successful! Please check your email to verify your account.');
};

// Email verification page
const VerifyEmailPage = () => {
  const [token] = useSearchParams();

  useEffect(() => {
    if (token) {
      graphqlClient.mutate({
        mutation: VERIFY_EMAIL_MUTATION,
        variables: { input: { token } }
      })
      .then(result => {
        if (result.data.verifyEmail.success) {
          alert('Email verified!');
          navigate('/dashboard');
        }
      });
    }
  }, [token]);

  return <div>Verifying your email...</div>;
};

// Password reset request
const RequestResetPage = () => {
  const [email, setEmail] = useState('');

  const handleSubmit = async () => {
    await graphqlClient.mutate({
      mutation: REQUEST_RESET_MUTATION,
      variables: { input: { email } }
    });

    alert('If this email exists, you will receive a reset link.');
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        placeholder="Enter your email"
      />
      <button type="submit">Send Reset Link</button>
    </form>
  );
};
```

---

## 🛠️ Troubleshooting

### Email не приходит

**Проверка:**
```bash
# 1. MailPit запущен?
docker ps | grep mailpit

# 2. Проверьте логи приложения
docker logs templates_app_dev | grep -i email

# 3. Проверьте переменные окружения
docker exec templates_app_dev env | grep SMTP
```

### Токен недействителен

**Проверка:**
```bash
# Проверьте токен в Redis
docker exec templates_redis redis-cli
> KEYS verify:*
> GET verify:YOUR_TOKEN
> TTL verify:YOUR_TOKEN
```

**Причины:**
- Токен истек (проверьте TTL)
- Токен уже использован (одноразовый)
- Redis перезапустился без persistence

### Rate limit блокирует

**Сброс:**
```bash
docker exec templates_redis redis-cli DEL rate:email:test@example.com
```

---

## 📚 Документация

- **Полный Flow**: [docs/EMAIL_VERIFICATION_FLOW.md](docs/EMAIL_VERIFICATION_FLOW.md)
- **Email Service**: [docs/EMAIL_SERVICE.md](docs/EMAIL_SERVICE.md)
- **MailPit**: [docs/MAILPIT_QUICKSTART.md](docs/MAILPIT_QUICKSTART.md)

---

## 🎯 Next Steps

### Обязательные для Production

- [ ] Настроить production SMTP (SendGrid/AWS SES)
- [ ] Усилить валидацию паролей
- [ ] Требовать email verification для login
- [ ] Добавить email notification при смене пароля
- [ ] Настроить Redis persistence в production

### Опциональные улучшения

- [ ] Добавить 2FA (TOTP)
- [ ] Welcome email после верификации
- [ ] Email при входе с нового устройства
- [ ] Admin панель для управления пользователями
- [ ] Метрики и мониторинг (Prometheus)
- [ ] Audit logs

---

## ✨ Готово!

Теперь ваш сервис полностью поддерживает:

1. ✅ Регистрацию с автоматической отправкой email верификации
2. ✅ Подтверждение email по ссылке из письма
3. ✅ Восстановление пароля через email
4. ✅ Rate limiting для предотвращения спама
5. ✅ Безопасное хранение токенов в Redis с TTL
6. ✅ Полное тестирование и документация

**Команды для быстрого старта:**

```bash
# Запустить
docker-compose -f docker-compose.dev.yml up -d

# Открыть GraphQL
open http://localhost:8000/graphql

# Открыть MailPit
open http://localhost:8025

# Тесты
pytest tests/test_email_verification.py -v
```

Happy coding! 🚀
