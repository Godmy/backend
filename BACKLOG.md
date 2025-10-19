# Product Backlog - МультиПУЛЬТ

Бэклог пользовательских историй для развития проекта в production-ready backend template.

## Легенда приоритетов

- 🔥 **P0** - Критически важно (блокирует production)
- ⚡ **P1** - Высокий приоритет (важно для пользователей)
- 📌 **P2** - Средний приоритет (улучшение UX)
- 💡 **P3** - Низкий приоритет (nice to have)

## Статусы

- 📋 **Backlog** - в очереди
- 🚧 **In Progress** - в разработке
- ✅ **Done** - завершено
- 🔒 **Blocked** - заблокировано

## 🎯 Vision: Production-Ready Template для тысяч проектов

**Цель:** Создать универсальный, безопасный, масштабируемый backend-шаблон, который может быть использован как submodule в любом проекте и запущен в production за 30 минут.

---

## Top 10 Приоритетных Задач

### 1. 🔥 P0 - File Upload System для Avatars и Attachments

**User Story:**
> Как пользователь, я хочу загружать аватар для профиля и прикреплять файлы к концепциям, чтобы визуально идентифицировать себя и добавлять медиа к контенту.

**Acceptance Criteria:**
- [✅] Загрузка файлов через GraphQL (multipart/form-data)
- [✅] Сохранение в локальное хранилище или S3
- [✅] Валидация типов файлов (JPEG, PNG, GIF для аватаров)
- [✅] Ограничение размера (5MB для аватаров, 10MB для attachments)
- [✅] Генерация thumbnails для изображений
- [✅] Secure filename sanitization
- [✅] GraphQL mutations: `uploadAvatar`, `uploadFile`, `deleteFile`
- [✅] Endpoint для получения файлов: `/uploads/:filename`

**Implementation:**
- `core/models/file.py` - модель File для БД
- `core/file_storage.py` - FileStorageService для работы с файловой системой
- `core/services/file_service.py` - бизнес-логика
- `core/schemas/file.py` - GraphQL API
- `app.py` - endpoint `/uploads/{filename:path}`
- Обновлена модель UserProfileModel с `avatar_file_id`
- Добавлен Pillow в requirements.txt

**Estimated Effort:** 5 story points

**Status:** ✅ **Done** (2025-01-16)

---

### 2. ⚡ P1 - Advanced Search & Filtering

**User Story:**
> Как пользователь, я хочу искать концепции и переводы по ключевым словам, фильтровать по языкам и тегам, чтобы быстро находить нужную информацию.

**Acceptance Criteria:**
- [ ] Full-text search по концепциям (name, description)
- [ ] Поиск по переводам в словарях
- [ ] Фильтры: язык, категория, дата создания
- [ ] Пагинация результатов (по 20 элементов)
- [ ] Сортировка: по релевантности, алфавиту, дате
- [ ] GraphQL query: `searchConcepts(query: String!, filters: SearchFilters)`
- [ ] PostgreSQL full-text search или интеграция с Elasticsearch

**Example Query:**
```graphql
query SearchConcepts {
  searchConcepts(
    query: "пользователь"
    filters: {
      languages: ["ru", "en"]
      dateFrom: "2024-01-01"
    }
    pagination: { limit: 20, offset: 0 }
    sortBy: RELEVANCE
  ) {
    results {
      id
      name
      translations {
        language { code }
        name
      }
    }
    totalCount
  }
}
```

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog

---

### 3. ⚡ P1 - User Profile Management

**User Story:**
> Как пользователь, я хочу управлять своим профилем (имя, био, аватар, настройки), чтобы персонализировать аккаунт.

**Acceptance Criteria:**
- [ ] GraphQL mutation: `updateProfile(input: ProfileUpdateInput!)`
- [ ] Поля: firstName, lastName, bio, avatar, timezone, language
- [ ] Валидация: bio до 500 символов
- [ ] Возможность изменить email (с подтверждением)
- [ ] Возможность изменить пароль (с текущим паролем)
- [ ] Просмотр истории OAuth подключений
- [ ] Отвязка OAuth провайдеров
- [ ] Удаление аккаунта (soft delete)

**Mutations:**
```graphql
mutation UpdateProfile {
  updateProfile(input: {
    firstName: "Иван"
    lastName: "Петров"
    bio: "Backend разработчик"
    timezone: "Europe/Moscow"
  }) {
    id
    firstName
    lastName
  }
}

mutation ChangeEmail {
  changeEmail(input: {
    newEmail: "newemail@example.com"
    password: "CurrentPass123!"
  }) {
    success
    message
    # Отправляет email на новый адрес для подтверждения
  }
}

mutation DeleteAccount {
  deleteAccount(input: {
    password: "CurrentPass123!"
    reason: "Не использую больше"
  }) {
    success
  }
}
```

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog

---

### 4. 🔥 P0 - Audit Logging System

**User Story:**
> Как администратор, я хочу видеть логи всех важных действий пользователей (вход, изменения данных, удаления), чтобы обеспечить безопасность и возможность аудита.

**Acceptance Criteria:**
- [✅] Новая модель `AuditLog` с полями: user_id, action, entity_type, entity_id, old_data, new_data, ip_address, user_agent, timestamp, description, status
- [✅] Готовые методы логирования: login, logout, register, OAuth login, entity CRUD
- [✅] GraphQL queries для админов: `auditLogs`, `myAuditLogs`, `userActivity`
- [✅] Фильтрация по user_id, action, entity_type, status, датам
- [✅] Пагинация и сортировка
- [✅] Метод автоматической очистки старых логов (`cleanup_old_logs`)
- [✅] Статистика активности пользователя

**Implementation:**
- `core/models/audit_log.py` - модель AuditLog
- `core/services/audit_service.py` - AuditService с методами:
  - `log()` - базовый метод логирования
  - `log_login()`, `log_register()`, `log_logout()`
  - `log_entity_create/update/delete()`
  - `get_logs()` - получение с фильтрами
  - `get_user_activity()` - статистика
  - `cleanup_old_logs()` - очистка
- `core/schemas/audit.py` - GraphQL API для аудита
- Интегрировано в core/schemas/schema.py

**Estimated Effort:** 8 story points

**Status:** ✅ **Done** (2025-01-16)

---

### 5. ⚡ P1 - API Rate Limiting

**User Story:**
> Как администратор, я хочу ограничить количество запросов к API от одного пользователя/IP, чтобы защититься от злоупотреблений и DDoS атак.

**Acceptance Criteria:**
- [ ] Rate limiting на уровне приложения (не только nginx)
- [ ] Лимиты на основе: IP адреса, user_id, JWT токена
- [ ] Разные лимиты для разных endpoint'ов:
  - Обычные запросы: 100 req/min
  - Мутации: 20 req/min
  - Login/register: 5 req/min
  - Email отправка: 3 req/hour (уже есть)
- [ ] Redis для хранения счетчиков
- [ ] HTTP заголовки: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- [ ] GraphQL error при превышении: `RATE_LIMIT_EXCEEDED`
- [ ] Белый список IP для админов

**Implementation:**
```python
# core/rate_limiter.py
from functools import wraps
from starlette.requests import Request

def rate_limit(max_requests: int, window_seconds: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('info').context['request']
            ip = request.client.host
            key = f"rate_limit:{ip}:{func.__name__}"

            # Check Redis counter
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, window_seconds)

            if current > max_requests:
                raise GraphQLError("Rate limit exceeded")

            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog

---

### 6. 📌 P2 - Soft Delete для всех моделей

**User Story:**
> Как администратор, я хочу восстанавливать случайно удаленные данные (пользователей, концепции, словари), вместо их окончательного удаления.

**Acceptance Criteria:**
- [ ] Добавить поля `deleted_at`, `deleted_by` в BaseModel
- [ ] Все DELETE операции помечают `deleted_at = now()`
- [ ] Фильтрация по умолчанию исключает deleted записи
- [ ] GraphQL query `archivedItems` для просмотра удаленных
- [ ] Мутация `restoreItem(id: ID!)` для восстановления
- [ ] Мутация `permanentlyDelete(id: ID!)` для админов
- [ ] Автоматическое permanent удаление через 90 дней

**BaseModel update:**
```python
# core/models/base.py
class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    @classmethod
    def active(cls):
        """Фильтр для неудаленных записей"""
        return cls.deleted_at.is_(None)
```

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog

---

### 7. ⚡ P1 - Import/Export System

**User Story:**
> Как администратор контента, я хочу экспортировать и импортировать концепции и переводы в JSON/CSV, чтобы мигрировать данные между окружениями или делать бэкапы.

**Acceptance Criteria:**
- [ ] GraphQL mutation: `exportData(entityType: String!, format: ExportFormat!)`
- [ ] Форматы: JSON, CSV, XLSX
- [ ] Экспорт: concepts, dictionaries, users (без паролей)
- [ ] Импорт с валидацией: `importData(file: Upload!, entityType: String!)`
- [ ] Обработка дубликатов: skip, update, or fail
- [ ] Асинхронная обработка для больших файлов
- [ ] Прогресс импорта через WebSocket или polling
- [ ] Лог импорта: успешные/ошибочные записи

**Example:**
```graphql
mutation ExportConcepts {
  exportData(
    entityType: "concepts"
    format: JSON
    filters: { language: "ru" }
  ) {
    url  # Ссылка на скачивание
    expiresAt
  }
}

mutation ImportConcepts {
  importData(
    file: Upload!
    entityType: "concepts"
    options: {
      onDuplicate: UPDATE
      validateOnly: false
    }
  ) {
    jobId
    status
  }
}

query ImportStatus {
  importJob(id: "job-123") {
    status  # pending, processing, completed, failed
    progress  # 75%
    processedCount
    errorCount
    errors {
      row
      message
    }
  }
}
```

**Estimated Effort:** 13 story points

**Status:** 📋 Backlog

---

### 8. 📌 P2 - Admin Panel Features

**User Story:**
> Как администратор, я хочу управлять пользователями, ролями и правами через GraphQL, чтобы контролировать доступ к системе.

**Acceptance Criteria:**
- [ ] GraphQL queries для админов:
  - `users(filters, pagination)` - список всех пользователей
  - `userActivity(userId)` - активность пользователя
  - `systemStats` - статистика системы
- [ ] Мутации:
  - `adminUpdateUser` - изменить данные любого пользователя
  - `adminBanUser` - заблокировать пользователя
  - `adminUnbanUser` - разблокировать
  - `adminAssignRole` - назначить роль
  - `adminRevokeRole` - отозвать роль
- [ ] Фильтры: по ролям, статусу (active/banned/unverified), дате регистрации
- [ ] Пагинация и сортировка
- [ ] Bulk операции: массовое удаление, изменение ролей

**Queries:**
```graphql
query AdminGetUsers {
  users(
    filters: {
      role: "user"
      status: ACTIVE
      registeredAfter: "2024-01-01"
    }
    pagination: { limit: 50, offset: 0 }
    sortBy: { field: CREATED_AT, order: DESC }
  ) {
    users {
      id
      username
      email
      roles { name }
      isVerified
      isBanned
      lastLoginAt
    }
    totalCount
  }
}

query SystemStats {
  systemStats {
    totalUsers
    activeUsers
    totalConcepts
    totalTranslations
    languagesCount
    storageUsed
  }
}

mutation AdminBanUser {
  adminBanUser(
    userId: 123
    reason: "Spam"
    until: "2024-12-31"
  ) {
    success
    message
  }
}
```

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog

---

### 9. 💡 P3 - GraphQL Subscriptions (Real-time Updates)

**User Story:**
> Как пользователь, я хочу получать обновления в реальном времени (новые переводы, изменения концепций), чтобы видеть актуальные данные без перезагрузки.

**Acceptance Criteria:**
- [ ] WebSocket поддержка в Strawberry GraphQL
- [ ] Subscriptions:
  - `conceptUpdated(conceptId)` - изменения концепции
  - `translationAdded(conceptId)` - новый перевод
  - `userStatusChanged(userId)` - статус пользователя online/offline
- [ ] Redis Pub/Sub для обмена сообщениями между workers
- [ ] Аутентификация через WebSocket (JWT в connection params)
- [ ] Graceful disconnect handling

**Implementation:**
```python
# В core/schemas/schema.py
@strawberry.type
class Subscription:
    @strawberry.subscription
    async def concept_updated(
        self,
        info: Info,
        concept_id: int
    ) -> ConceptType:
        async for message in redis_subscribe(f"concept:{concept_id}"):
            yield message

# Клиент
subscription {
  conceptUpdated(conceptId: 123) {
    id
    name
    updatedAt
    dictionaries {
      language { code }
      name
    }
  }
}
```

**Estimated Effort:** 13 story points

**Status:** 📋 Backlog

---

### 10. 📌 P2 - Notification System

**User Story:**
> Как пользователь, я хочу получать уведомления о важных событиях (новые комментарии, изменения в концепциях, которые я отслеживаю), чтобы быть в курсе.

**Acceptance Criteria:**
- [ ] Модель `Notification`: type, title, message, is_read, user_id, entity_type, entity_id
- [ ] Типы уведомлений:
  - `concept_updated` - изменена отслеживаемая концепция
  - `translation_added` - добавлен перевод
  - `comment_reply` - ответ на комментарий
  - `role_assigned` - назначена новая роль
  - `system_announcement` - системное объявление
- [ ] Доставка: in-app, email, web push (опционально)
- [ ] GraphQL queries:
  - `notifications(filters, pagination)` - список уведомлений
  - `unreadNotificationsCount` - количество непрочитанных
- [ ] Мутации:
  - `markNotificationAsRead(id)`
  - `markAllAsRead`
  - `deleteNotification(id)`
- [ ] Настройки пользователя: какие уведомления получать

**Models:**
```python
# core/models/notification.py
class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    entity_type = Column(String(50))  # "concept", "comment"
    entity_id = Column(Integer)
    data = Column(JSON)  # Дополнительные данные

    user = relationship("User", backref="notifications")

class NotificationSettings(BaseModel):
    __tablename__ = "notification_settings"

    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    email_notifications = Column(Boolean, default=True)
    concept_updates = Column(Boolean, default=True)
    translation_updates = Column(Boolean, default=True)
    comments = Column(Boolean, default=True)
    system_announcements = Column(Boolean, default=True)
```

**Queries:**
```graphql
query GetNotifications {
  notifications(
    filters: { isRead: false }
    pagination: { limit: 20, offset: 0 }
  ) {
    notifications {
      id
      type
      title
      message
      isRead
      createdAt
      entity {
        ... on ConceptType {
          id
          name
        }
      }
    }
    totalCount
    unreadCount
  }
}

mutation MarkAsRead {
  markNotificationAsRead(id: 123) {
    success
  }
}
```

**Estimated Effort:** 13 story points

**Status:** 📋 Backlog

---

## Дополнительные задачи (P3 - Nice to Have)

### 11. 💡 P3 - Two-Factor Authentication (2FA)

**User Story:**
> Как пользователь, я хочу включить двухфакторную аутентификацию для дополнительной безопасности аккаунта.

**Acceptance Criteria:**
- [ ] TOTP (Time-based One-Time Password) через Google Authenticator/Authy
- [ ] QR код для настройки
- [ ] Backup коды (10 одноразовых кодов)
- [ ] Принудительная 2FA для админов
- [ ] Recovery опции при потере устройства

**Estimated Effort:** 8 story points

---

### 12. 💡 P3 - Comment System для концепций

**User Story:**
> Как пользователь, я хочу оставлять комментарии к концепциям и переводам, чтобы обсуждать их с другими.

**Acceptance Criteria:**
- [ ] Модель `Comment` с вложенными комментариями (threads)
- [ ] CRUD операции через GraphQL
- [ ] Markdown поддержка
- [ ] Модерация комментариев (для moderator роли)
- [ ] Уведомления о новых комментариях

**Estimated Effort:** 13 story points

---

### 13. 💡 P3 - Version History для концепций

**User Story:**
> Как редактор, я хочу видеть историю изменений концепций и переводов, чтобы откатывать ошибочные правки.

**Acceptance Criteria:**
- [ ] Модель `ConceptVersion` с snapshot данных
- [ ] Автоматическое создание версии при каждом изменении
- [ ] Просмотр diff между версиями
- [ ] Откат к предыдущей версии
- [ ] Хранение не более 50 последних версий

**Estimated Effort:** 13 story points

---

### 14. 💡 P3 - Tags/Labels система

**User Story:**
> Как редактор, я хочу добавлять теги к концепциям для лучшей организации и поиска.

**Acceptance Criteria:**
- [ ] Модель `Tag` с many-to-many связью с Concept
- [ ] CRUD операции для тегов
- [ ] Автокомплит при добавлении тега
- [ ] Поиск концепций по тегам
- [ ] Цветовая маркировка тегов

**Estimated Effort:** 5 story points

---

### 15. 💡 P3 - Analytics Dashboard

**User Story:**
> Как администратор, я хочу видеть аналитику использования системы (популярные концепции, активные пользователи, языки).

**Acceptance Criteria:**
- [ ] Dashboard с метриками:
  - Регистрации по дням
  - Активные пользователи (DAU, MAU)
  - Топ-10 популярных концепций
  - Использование языков
  - API requests statistics
- [ ] Графики с Chart.js или Recharts
- [ ] Экспорт отчетов в PDF

**Estimated Effort:** 13 story points

---

## Процесс работы с бэклогом

### Планирование спринта

1. **Grooming** - еженедельный разбор задач:
   - Уточнение требований
   - Оценка сложности (story points)
   - Приоритизация

2. **Sprint Planning** - выбор задач на спринт:
   - Capacity: ~20 story points на спринт
   - Выбор из топ-приоритетных задач
   - Декомпозиция на подзадачи

3. **Daily** - обновление статусов

4. **Review & Retro** - демо и ретроспектива

### Критерии готовности (Definition of Done)

- [ ] Код написан и прошел code review
- [ ] Unit тесты написаны и проходят
- [ ] Integration тесты проходят
- [ ] Документация обновлена (CLAUDE.md, README.md)
- [ ] GraphQL schema экспортирована
- [ ] Миграции созданы (если нужны)
- [ ] Проверено на staging окружении
- [ ] No regressions в существующем функционале

---

## Метрики

**Velocity:** Отслеживать завершенные story points за спринт

**Sprint Goal Achievement:** % выполненных задач из sprint backlog

**Bug Rate:** Количество багов на задачу

---

---

## 🚀 НОВЫЕ ЗАДАЧИ: Infrastructure & Production Readiness

### 16. 🔥 P0 - Error Tracking & Monitoring (Sentry Integration)

**User Story:**
> Как DevOps инженер, я хочу автоматически отслеживать все ошибки в production, чтобы быстро реагировать на проблемы.

**Acceptance Criteria:**
- [✅] Интеграция с Sentry (или аналог)
- [✅] Автоматическая отправка всех uncaught exceptions
- [✅] Контекст ошибок: user_id, request_id, endpoint, environment
- [✅] Source maps для stack traces
- [✅] Email/Slack уведомления при критических ошибках (настраивается в Sentry UI)
- [✅] Группировка похожих ошибок (автоматически в Sentry)
- [✅] Performance monitoring (transaction traces)
- [✅] Release tracking для связи с деплоями
- [✅] Breadcrumbs для отслеживания действий пользователя
- [✅] Фильтрация чувствительных данных (пароли, токены)

**Implementation:**
```python
# core/sentry.py
import sentry_sdk
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

def init_sentry():
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        environment=os.getenv("ENVIRONMENT", "production"),
        traces_sample_rate=1.0,
        integrations=[
            StarletteIntegration(),
            SqlalchemyIntegration(),
        ],
        before_send=filter_sensitive_data,
    )

# В app.py
from core.sentry import init_sentry
init_sentry()
```

**Dependencies:** `sentry-sdk[starlette,sqlalchemy]`, `psutil`

**Implementation Details:**
- `core/sentry.py` - Sentry initialization with integrations (Starlette, SQLAlchemy, Logging)
- `app.py` - Automatic initialization on startup
- Environment variables: SENTRY_DSN, ENVIRONMENT, SENTRY_ENABLE_TRACING, SENTRY_TRACES_SAMPLE_RATE
- Automatic user context tracking for authenticated requests
- Comprehensive tests in `tests/test_sentry.py`
- Documentation in CLAUDE.md with setup instructions and usage examples
- Production checklist updated with Sentry configuration steps

**Key Features Implemented:**
- `before_send` filter for automatic sensitive data removal
- User context tracking with username and email
- Breadcrumbs for authenticated requests
- Configurable sample rates (1.0 for dev, 0.1 for production)
- Manual error capture: `capture_exception()`, `capture_message()`
- Performance monitoring: `start_transaction()`
- Helper functions: `set_user_context()`, `add_breadcrumb()`, `set_context()`

**Estimated Effort:** 5 story points

**Status:** ✅ **Done** (2025-01-19)

---

### 17. 🔥 P0 - Prometheus Metrics Collection

**User Story:**
> Как SRE, я хочу собирать метрики производительности (latency, throughput, errors), чтобы настраивать алерты и анализировать тренды.

**Acceptance Criteria:**
- [ ] Экспорт метрик в формате Prometheus
- [ ] Endpoint `/metrics` для scraping
- [ ] Метрики запросов:
  - `http_requests_total` (counter)
  - `http_request_duration_seconds` (histogram)
  - `http_requests_in_progress` (gauge)
- [ ] Метрики GraphQL:
  - `graphql_query_duration_seconds`
  - `graphql_query_errors_total`
  - `graphql_query_complexity`
- [ ] Метрики базы данных:
  - `db_connections_active`
  - `db_query_duration_seconds`
  - `db_errors_total`
- [ ] Метрики Redis:
  - `redis_connections_active`
  - `redis_commands_total`
- [ ] Метрики бизнес-логики:
  - `users_registered_total`
  - `emails_sent_total`
  - `files_uploaded_total`
- [ ] Метрики системы:
  - `process_cpu_usage`
  - `process_memory_bytes`
  - `process_open_fds`
- [ ] Grafana dashboard template

**Implementation:**
```python
# core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'Request duration')
DB_CONNECTIONS = Gauge('db_connections_active', 'Active DB connections')

# middleware/metrics.py
class PrometheusMiddleware:
    async def __call__(self, request, call_next):
        with REQUEST_DURATION.time():
            response = await call_next(request)
        REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
        return response

# app.py
@app.route("/metrics")
async def metrics(request):
    return Response(generate_latest(), media_type="text/plain")
```

**Dependencies:** `prometheus-client`, `prometheus-fastapi-instrumentator`

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog

---

### 18. 🔥 P0 - Background Task Processing (Celery)

**User Story:**
> Как разработчик, я хочу выполнять длительные задачи асинхронно (отправка email, генерация отчетов), чтобы не блокировать API запросы.

**Acceptance Criteria:**
- [ ] Celery setup с Redis/RabbitMQ broker
- [ ] Worker процесс в Docker Compose
- [ ] Задачи:
  - `send_email_task` - отправка email
  - `cleanup_old_logs_task` - очистка старых audit logs
  - `generate_report_task` - генерация отчетов
  - `process_image_task` - обработка изображений
  - `send_notification_task` - отправка уведомлений
- [ ] Scheduled tasks (Celery Beat):
  - Ежедневная очистка старых токенов
  - Еженедельная генерация статистики
  - Ежемесячный бэкап данных
- [ ] Retry механизм с exponential backoff
- [ ] Task monitoring через Flower
- [ ] Task result backend (Redis)
- [ ] GraphQL query для статуса задачи: `taskStatus(taskId: ID!)`
- [ ] Dead letter queue для failed tasks
- [ ] Rate limiting на уровне задач

**Implementation:**
```python
# core/celery_app.py
from celery import Celery

celery_app = Celery(
    "multipult",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# tasks/email_tasks.py
@celery_app.task(bind=True, max_retries=3)
def send_email_task(self, to: str, subject: str, body: str):
    try:
        send_email(to, subject, body)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

# tasks/cleanup_tasks.py
@celery_app.task
def cleanup_old_logs():
    AuditService.cleanup_old_logs(days=90)

# Celery Beat schedule
celery_app.conf.beat_schedule = {
    'cleanup-logs-daily': {
        'task': 'tasks.cleanup_tasks.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

**Dependencies:** `celery[redis]`, `flower`

**Docker Compose:**
```yaml
services:
  celery_worker:
    build: .
    command: celery -A core.celery_app worker --loglevel=info
    depends_on:
      - redis
      - db

  celery_beat:
    build: .
    command: celery -A core.celery_app beat --loglevel=info
    depends_on:
      - redis

  flower:
    build: .
    command: celery -A core.celery_app flower --port=5555
    ports:
      - "5555:5555"
```

**Estimated Effort:** 13 story points

**Status:** 📋 Backlog

---

### 19. 🔥 P0 - Structured Logging (JSON Format)

**User Story:**
> Как DevOps инженер, я хочу иметь структурированные логи в JSON формате, чтобы легко их агрегировать и анализировать в ELK/CloudWatch.

**Acceptance Criteria:**
- [ ] JSON formatter для логов
- [ ] Поля в каждом логе:
  - `timestamp` (ISO 8601)
  - `level` (INFO, WARNING, ERROR)
  - `message`
  - `service` (backend)
  - `environment` (dev/staging/prod)
  - `request_id` (correlation ID)
  - `user_id` (если аутентифицирован)
  - `endpoint` (GraphQL query/mutation)
  - `duration_ms` (для запросов)
  - `error` (stack trace если есть)
- [ ] Контекстные логи с дополнительными полями
- [ ] Log levels конфигурируются через env
- [ ] Ротация логов (по размеру/дате)
- [ ] Separate log streams: access, error, audit
- [ ] Фильтрация sensitive данных (tokens, passwords)

**Implementation:**
```python
# core/logging_config.py
import logging
import json
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['service'] = 'backend'
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(CustomJsonFormatter())

    logging.basicConfig(
        level=os.getenv('LOG_LEVEL', 'INFO'),
        handlers=[handler]
    )

# middleware/request_id.py
import uuid

class RequestIDMiddleware:
    async def __call__(self, request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers['X-Request-ID'] = request.state.request_id
        return response

# Использование в сервисах
logger.info("User logged in", extra={
    'user_id': user.id,
    'request_id': request.state.request_id,
    'ip_address': request.client.host
})
```

**Dependencies:** `python-json-logger`

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog

---

### 20. 🔥 P0 - Request ID & Distributed Tracing

**User Story:**
> Как разработчик, я хочу отслеживать запросы через все сервисы (API → DB → Redis → Celery), чтобы находить bottlenecks.

**Acceptance Criteria:**
- [ ] Request ID генерируется для каждого запроса
- [ ] Request ID в headers: `X-Request-ID`
- [ ] Request ID в логах всех компонентов
- [ ] Request ID передается в Celery tasks
- [ ] OpenTelemetry интеграция (опционально)
- [ ] Jaeger/Zipkin для визуализации traces (опционально)
- [ ] Trace spans для:
  - GraphQL query/mutation
  - Database queries
  - Redis operations
  - External API calls
  - Celery tasks
- [ ] Correlation ID для связи между requests

**Implementation:** см. задачу 19 (RequestIDMiddleware)

**Dependencies:** `opentelemetry-api`, `opentelemetry-instrumentation-starlette` (опционально)

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog

---

### 21. ⚡ P1 - Application-Level Rate Limiting

**User Story:**
> Как backend разработчик, я хочу иметь rate limiting на уровне приложения (не только nginx), чтобы защититься от abuse на уровне пользователей и API endpoints.

**Acceptance Criteria:**
- [ ] Decorator для rate limiting на мутациях/queries
- [ ] Redis-backed счетчики
- [ ] Лимиты по:
  - IP адресу
  - User ID
  - API key (если есть)
- [ ] Конфигурируемые лимиты для разных endpoints:
  - `@rate_limit(max_requests=100, window_seconds=60)` - обычные запросы
  - `@rate_limit(max_requests=5, window_seconds=60)` - auth endpoints
  - `@rate_limit(max_requests=10, window_seconds=3600)` - file uploads
- [ ] HTTP headers в ответе:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`
- [ ] GraphQL error: `RATE_LIMIT_EXCEEDED`
- [ ] Whitelist для admin users
- [ ] Sliding window algorithm
- [ ] Metrics для rate limit hits

**Implementation:**
```python
# core/rate_limiter.py
from functools import wraps
from core.redis_client import redis_client

def rate_limit(max_requests: int, window_seconds: int, key_func=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            info = kwargs.get('info')
            request = info.context['request']
            user = info.context.get('user')

            # Определяем ключ для rate limit
            if key_func:
                key = key_func(request, user)
            elif user:
                key = f"rate_limit:{func.__name__}:user:{user.id}"
            else:
                key = f"rate_limit:{func.__name__}:ip:{request.client.host}"

            # Проверяем лимит
            current = await redis_client.incr(key)
            if current == 1:
                await redis_client.expire(key, window_seconds)

            ttl = await redis_client.ttl(key)

            # Добавляем headers в response
            info.context['response'].headers['X-RateLimit-Limit'] = str(max_requests)
            info.context['response'].headers['X-RateLimit-Remaining'] = str(max(0, max_requests - current))
            info.context['response'].headers['X-RateLimit-Reset'] = str(time.time() + ttl)

            if current > max_requests:
                raise GraphQLError(
                    "Rate limit exceeded",
                    extensions={"code": "RATE_LIMIT_EXCEEDED"}
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Использование
@strawberry.mutation
@rate_limit(max_requests=5, window_seconds=60)
async def login(self, info: Info, input: LoginInput) -> AuthPayload:
    ...
```

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog

---

### 22. ⚡ P1 - HTTP Caching Headers Middleware

**User Story:**
> Как разработчик, я хочу автоматически добавлять HTTP caching headers (ETag, Cache-Control), чтобы снизить нагрузку и ускорить ответы.

**Acceptance Criteria:**
- [ ] ETag generation для GET запросов
- [ ] `If-None-Match` header support (304 Not Modified)
- [ ] `Cache-Control` headers:
  - `public, max-age=3600` для публичных данных
  - `private, max-age=300` для user-specific данных
  - `no-cache` для sensitive данных
- [ ] `Last-Modified` header для ресурсов
- [ ] `Vary` header для content negotiation
- [ ] Конфигурация через decorators
- [ ] Cache invalidation при обновлении данных
- [ ] Support для `If-Modified-Since`

**Implementation:**
```python
# middleware/caching.py
import hashlib

class CachingMiddleware:
    async def __call__(self, request, call_next):
        # Только для GET запросов
        if request.method != "GET":
            return await call_next(request)

        response = await call_next(request)

        # Генерируем ETag из body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        etag = hashlib.md5(body).hexdigest()

        # Проверяем If-None-Match
        if request.headers.get("If-None-Match") == etag:
            return Response(status_code=304)

        # Добавляем headers
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "public, max-age=300"

        return response

# Для GraphQL можно использовать cache hints
@strawberry.type
class Language:
    @strawberry.field
    @cache_control(max_age=3600)  # Кастомный decorator
    def name(self) -> str:
        return self.name
```

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog

---

### 23. ⚡ P1 - Input Validation & Sanitization Middleware

**User Story:**
> Как security engineer, я хочу автоматически валидировать и sanitize все входные данные, чтобы защититься от injection attacks.

**Acceptance Criteria:**
- [ ] Schema validation на всех inputs
- [ ] HTML/SQL injection protection
- [ ] XSS protection (sanitize HTML tags)
- [ ] Path traversal protection (для file paths)
- [ ] Email validation
- [ ] URL validation
- [ ] Size limits для всех полей
- [ ] Regex validation для custom fields
- [ ] Blacklist опасных символов
- [ ] Normalization (trim, lowercase для emails)

**Implementation:**
```python
# core/validators.py
import bleach
import re

def sanitize_html(text: str) -> str:
    """Удаляет HTML теги"""
    return bleach.clean(text, strip=True)

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_filename(filename: str) -> str:
    """Удаляет опасные символы из имени файла"""
    return re.sub(r'[^\w\s.-]', '', filename)

# Использование в Strawberry input types
@strawberry.input
class CreateConceptInput:
    name: str
    description: str | None = None

    def __post_init__(self):
        # Валидация и sanitization
        self.name = sanitize_html(self.name.strip())
        if len(self.name) > 255:
            raise ValueError("Name too long")

        if self.description:
            self.description = sanitize_html(self.description.strip())
```

**Dependencies:** `bleach`, `validators`

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog

---

### 24. ⚡ P1 - Database Query Optimization & N+1 Prevention

**User Story:**
> Как backend разработчик, я хочу автоматически предотвращать N+1 queries, чтобы не деградировала производительность.

**Acceptance Criteria:**
- [ ] SQLAlchemy query logging в development
- [ ] Автоматическое использование `joinedload`/`selectinload`
- [ ] Query analyzer для обнаружения N+1
- [ ] Database indexes для всех foreign keys
- [ ] Composite indexes для частых queries
- [ ] Query result caching (Redis)
- [ ] Database connection pool monitoring
- [ ] Slow query detection (>100ms warning)
- [ ] Query explain plans в логах (dev mode)

**Implementation:**
```python
# core/database.py
import logging

# Enable query logging in dev
if os.getenv('DEBUG') == 'True':
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Middleware для подсчета queries
class QueryCounterMiddleware:
    async def __call__(self, request, call_next):
        from sqlalchemy import event

        query_count = 0

        def count_query(conn, cursor, statement, *args):
            nonlocal query_count
            query_count += 1

        event.listen(engine, "before_cursor_execute", count_query)

        response = await call_next(request)

        if query_count > 10:
            logger.warning(f"High query count: {query_count} queries")

        response.headers['X-Query-Count'] = str(query_count)

        event.remove(engine, "before_cursor_execute", count_query)

        return response

# Использование eager loading
def get_concepts_with_translations(db: Session):
    return db.query(ConceptModel).options(
        joinedload(ConceptModel.dictionaries).joinedload(DictionaryModel.language)
    ).all()
```

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog

---

### 25. 📌 P2 - API Versioning Support

**User Story:**
> Как API consumer, я хочу иметь версионирование API, чтобы обновления не ломали мою интеграцию.

**Acceptance Criteria:**
- [ ] URL-based versioning: `/graphql/v1`, `/graphql/v2`
- [ ] Header-based versioning: `X-API-Version: 1`
- [ ] Schema stitching для поддержки нескольких версий
- [ ] Deprecation warnings в responses
- [ ] Версионирование мутаций и типов
- [ ] Автоматическая генерация changelog между версиями
- [ ] Sunset headers для deprecated versions

**Implementation:**
```python
# schemas/v1/schema.py
schema_v1 = strawberry.Schema(query=Query, mutation=Mutation)

# schemas/v2/schema.py
schema_v2 = strawberry.Schema(query=QueryV2, mutation=MutationV2)

# app.py
app.mount("/graphql/v1", GraphQLWithContext(schema_v1))
app.mount("/graphql/v2", GraphQLWithContext(schema_v2))
app.mount("/graphql", GraphQLWithContext(schema_v2))  # Latest
```

**Estimated Effort:** 13 story points

**Status:** 📋 Backlog

---

### 26. 📌 P2 - GraphQL Query Complexity Analysis

**User Story:**
> Как backend developer, я хочу ограничивать сложность GraphQL запросов, чтобы защититься от DoS через complex queries.

**Acceptance Criteria:**
- [ ] Query complexity calculation
- [ ] Max complexity limit (например, 1000)
- [ ] Depth limit (например, 10 уровней)
- [ ] Cost analysis для каждого поля
- [ ] Rejection сложных queries с понятным error message
- [ ] Whitelist для admin users
- [ ] Metrics для query complexity

**Implementation:**
```python
# core/query_complexity.py
from strawberry.extensions import Extension

class QueryComplexityExtension(Extension):
    def on_request_start(self):
        complexity = self.calculate_complexity(self.execution_context.query)
        if complexity > 1000:
            raise GraphQLError(f"Query too complex: {complexity}")

schema = strawberry.Schema(
    query=Query,
    extensions=[QueryComplexityExtension]
)
```

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog

---

### 27. 📌 P2 - Automated Database Backup & Restore

**User Story:**
> Как DevOps engineer, я хочу автоматические бэкапы БД с возможностью восстановления, чтобы защититься от потери данных.

**Acceptance Criteria:**
- [ ] Scheduled daily backups (через Celery Beat)
- [ ] Incremental backups каждый час
- [ ] Full backup каждую неделю
- [ ] Backup retention policy (30 дней)
- [ ] Backup в S3/GCS/Azure Blob
- [ ] Backup encryption
- [ ] Restore скрипт с валидацией
- [ ] Backup verification (test restore)
- [ ] Metrics для backup size и duration
- [ ] Alerts при failed backups

**Implementation:**
```python
# tasks/backup_tasks.py
@celery_app.task
def backup_database():
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"backup_{timestamp}.sql.gz"

    # pg_dump
    os.system(f"pg_dump {DATABASE_URL} | gzip > /tmp/{filename}")

    # Upload to S3
    s3_client.upload_file(f"/tmp/{filename}", "backups", filename)

    # Cleanup old backups
    cleanup_old_backups(days=30)

# Celery Beat schedule
celery_app.conf.beat_schedule['backup-daily'] = {
    'task': 'tasks.backup_tasks.backup_database',
    'schedule': crontab(hour=3, minute=0),
}
```

**Dependencies:** `boto3` (для S3)

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog

---

### 28. 📌 P2 - Secrets Management (Vault Integration)

**User Story:**
> Как security engineer, я хочу хранить secrets в Vault/AWS Secrets Manager, а не в .env файлах.

**Acceptance Criteria:**
- [ ] HashiCorp Vault integration
- [ ] AWS Secrets Manager support (альтернатива)
- [ ] Secrets rotation без restart
- [ ] Environment-specific secrets
- [ ] Audit log для secret access
- [ ] Emergency secrets rotation
- [ ] Secrets версионирование
- [ ] Fallback на environment variables

**Implementation:**
```python
# core/secrets.py
import hvac

class SecretsManager:
    def __init__(self):
        self.vault_client = hvac.Client(
            url=os.getenv('VAULT_URL'),
            token=os.getenv('VAULT_TOKEN')
        )

    def get_secret(self, key: str) -> str:
        try:
            response = self.vault_client.secrets.kv.read_secret_version(path=key)
            return response['data']['data']['value']
        except Exception:
            # Fallback на env
            return os.getenv(key)

secrets = SecretsManager()
JWT_SECRET_KEY = secrets.get_secret('jwt_secret_key')
```

**Dependencies:** `hvac` (Vault client)

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog

---

### 29. 💡 P3 - Multi-Tenancy Support

**User Story:**
> Как SaaS provider, я хочу поддерживать multi-tenancy (несколько организаций в одной БД), чтобы снизить infrastructure costs.

**Acceptance Criteria:**
- [ ] Модель `Organization`/`Tenant`
- [ ] Row-level security для tenant isolation
- [ ] Tenant context в каждом запросе
- [ ] Tenant-specific subdomain routing
- [ ] Tenant-specific settings/branding
- [ ] Tenant usage metrics
- [ ] Tenant data export
- [ ] Cross-tenant admin queries (для super admin)

**Implementation:**
```python
# auth/models/organization.py
class Organization(BaseModel):
    __tablename__ = "organizations"
    name = Column(String(255), unique=True)
    subdomain = Column(String(100), unique=True)
    settings = Column(JSON)

# User с tenant
class User(BaseModel):
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    organization = relationship("Organization")

# Middleware для tenant context
class TenantMiddleware:
    async def __call__(self, request, call_next):
        subdomain = request.url.hostname.split('.')[0]
        org = db.query(Organization).filter_by(subdomain=subdomain).first()
        request.state.tenant = org
        return await call_next(request)

# Query filter
def get_users_for_tenant(db, tenant_id):
    return db.query(User).filter_by(organization_id=tenant_id).all()
```

**Estimated Effort:** 21 story points

**Status:** 📋 Backlog

---

### 30. 💡 P3 - Feature Flags System

**User Story:**
> Как product manager, я хочу включать/выключать фичи без деплоя, чтобы безопасно тестировать новые возможности.

**Acceptance Criteria:**
- [ ] Feature flags таблица в БД
- [ ] Feature flags admin UI
- [ ] Feature flags по:
  - Environment (dev/staging/prod)
  - User ID
  - User role
  - Percentage rollout (canary)
- [ ] Decorator `@feature_flag("new_feature")`
- [ ] GraphQL query: `isFeatureEnabled(name: String!)`
- [ ] Real-time feature flag updates (без restart)
- [ ] A/B testing support
- [ ] Feature flag analytics

**Implementation:**
```python
# core/models/feature_flag.py
class FeatureFlag(BaseModel):
    __tablename__ = "feature_flags"
    name = Column(String(100), unique=True)
    enabled = Column(Boolean, default=False)
    rollout_percentage = Column(Integer, default=0)  # 0-100
    enabled_for_roles = Column(ARRAY(String))
    enabled_for_users = Column(ARRAY(Integer))

# core/feature_flags.py
def is_feature_enabled(name: str, user=None) -> bool:
    flag = db.query(FeatureFlag).filter_by(name=name).first()
    if not flag:
        return False

    if flag.enabled:
        return True

    if user and user.id in flag.enabled_for_users:
        return True

    if user and user.role in flag.enabled_for_roles:
        return True

    # Percentage rollout
    if flag.rollout_percentage > 0:
        user_hash = hash(user.id) if user else 0
        return (user_hash % 100) < flag.rollout_percentage

    return False

# Использование
@strawberry.mutation
def create_concept(self, info: Info, input: CreateConceptInput):
    if is_feature_enabled("new_concept_validation", info.context.get('user')):
        # New validation logic
        pass
    else:
        # Old logic
        pass
```

**Estimated Effort:** 13 story points

**Status:** 📋 Backlog

---

### 31. 💡 P3 - WebSocket Support для Real-time Updates

**User Story:**
> Как frontend developer, я хочу получать real-time обновления через WebSocket, чтобы не делать polling.

**Acceptance Criteria:**
- [ ] WebSocket endpoint `/ws`
- [ ] Authentication через WebSocket (JWT в connection params)
- [ ] Subscribe/Unsubscribe mechanism
- [ ] Channels:
  - `user.{user_id}` - личные уведомления
  - `concept.{concept_id}` - обновления концепции
  - `system` - системные объявления
- [ ] Redis Pub/Sub для multi-server support
- [ ] Heartbeat/ping-pong для connection health
- [ ] Reconnection logic на клиенте
- [ ] Rate limiting для WS messages

**Implementation:**
```python
# core/websocket.py
from starlette.websockets import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)

    async def send_to_channel(self, channel: str, message: dict):
        if channel in self.active_connections:
            for connection in self.active_connections[channel]:
                await connection.send_json(message)

manager = ConnectionManager()

# app.py
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "system")
    try:
        while True:
            data = await websocket.receive_json()
            # Handle subscribe/unsubscribe
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

**Estimated Effort:** 13 story points

**Status:** 📋 Backlog

---

### 32. ⚡ P1 - Enhanced Health Checks

**User Story:**
> Как DevOps engineer, я хочу детальные health checks для всех зависимостей, чтобы быстро диагностировать проблемы.

**Acceptance Criteria:**
- [ ] `/health` - overall health (200/503)
- [ ] `/health/detailed` - статус всех компонентов
- [ ] Проверки:
  - Database connectivity + query test
  - Redis connectivity + ping
  - Disk space available (>10% free)
  - Memory usage (<90%)
  - Celery workers alive
  - External API dependencies (если есть)
- [ ] Response format:
```json
{
  "status": "healthy",
  "version": "0.3.0",
  "uptime_seconds": 12345,
  "checks": {
    "database": {"status": "healthy", "latency_ms": 5},
    "redis": {"status": "healthy", "latency_ms": 2},
    "disk": {"status": "healthy", "free_percent": 45},
    "memory": {"status": "warning", "used_percent": 85},
    "celery": {"status": "healthy", "workers": 2}
  }
}
```
- [ ] `/health/liveness` - для Kubernetes liveness probe
- [ ] `/health/readiness` - для Kubernetes readiness probe

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog

---

### 33. 📌 P2 - API Documentation Generator (OpenAPI/Swagger)

**User Story:**
> Как API consumer, я хочу иметь OpenAPI spec для REST endpoints, чтобы генерировать клиенты автоматически.

**Acceptance Criteria:**
- [ ] Auto-generated OpenAPI spec для REST endpoints
- [ ] `/openapi.json` endpoint
- [ ] Swagger UI на `/docs`
- [ ] ReDoc на `/redoc`
- [ ] GraphQL schema экспорт на `/graphql/schema`
- [ ] Postman collection generator
- [ ] Examples для всех endpoints
- [ ] Authentication section в docs

**Implementation:**
```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

# Если добавим REST endpoints
rest_app = FastAPI()

@rest_app.get("/api/v1/users/{user_id}")
def get_user(user_id: int):
    """Get user by ID"""
    ...

# Mount REST app alongside GraphQL
app.mount("/api", rest_app)
```

**Dependencies:** `fastapi` (если добавим REST)

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog

---

### 34. ⚡ P1 - Data Migration Tools

**User Story:**
> Как developer, я хочу иметь инструменты для безопасной миграции данных между версиями, чтобы не потерять данные при обновлениях.

**Acceptance Criteria:**
- [ ] Data migration framework (отдельно от schema migrations)
- [ ] Reversible migrations (up/down)
- [ ] Migration validation перед apply
- [ ] Dry-run mode
- [ ] Progress reporting для длительных миграций
- [ ] Rollback mechanism
- [ ] Migration locking (prevent concurrent runs)
- [ ] Migration audit log

**Implementation:**
```python
# migrations/data/001_migrate_user_roles.py
class MigrateUserRoles:
    def up(self, db: Session):
        # Migrate data forward
        users = db.query(User).filter_by(old_role="moderator").all()
        for user in users:
            user.role_id = new_moderator_role.id
        db.commit()

    def down(self, db: Session):
        # Rollback migration
        users = db.query(User).filter_by(role_id=new_moderator_role.id).all()
        for user in users:
            user.old_role = "moderator"
        db.commit()

# scripts/run_data_migration.py
python run_data_migration.py --migration 001 --dry-run
python run_data_migration.py --migration 001 --apply
```

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog

---

### 35. 📌 P2 - API Client SDK Generator

**User Story:**
> Как frontend developer, я хочу иметь auto-generated клиент для GraphQL, чтобы не писать queries вручную.

**Acceptance Criteria:**
- [ ] GraphQL Code Generator setup
- [ ] TypeScript types для всех GraphQL типов
- [ ] React hooks для queries/mutations (если React frontend)
- [ ] Python client SDK для backend-to-backend
- [ ] Auto-regeneration при schema changes
- [ ] Published SDK package (npm/pypi)
- [ ] SDK documentation

**Implementation:**
```yaml
# codegen.yml
schema: http://localhost:8000/graphql
documents: 'src/**/*.graphql'
generates:
  src/generated/graphql.ts:
    plugins:
      - typescript
      - typescript-operations
      - typescript-react-apollo
```

**Dependencies:** `@graphql-codegen/cli`

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog

---

### 36. 💡 P3 - Load Testing Framework

**User Story:**
> Как QA engineer, я хочу иметь готовые load tests, чтобы валидировать производительность перед production.

**Acceptance Criteria:**
- [ ] Locust/K6 setup
- [ ] Test scenarios:
  - Login flow (100 users/sec)
  - Read-heavy queries (500 req/sec)
  - Write-heavy mutations (50 req/sec)
  - File upload (10 concurrent)
- [ ] CI integration для performance regression tests
- [ ] Performance benchmarks baseline
- [ ] Reports с latency percentiles (p50, p95, p99)

**Implementation:**
```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class GraphQLUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login
        response = self.client.post("/graphql", json={
            "query": "mutation { login(input: {username: \"test\", password: \"test\"}) { accessToken } }"
        })
        self.token = response.json()['data']['login']['accessToken']

    @task(3)
    def get_languages(self):
        self.client.post("/graphql",
            json={"query": "query { languages { id name } }"},
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(1)
    def create_concept(self):
        self.client.post("/graphql",
            json={"query": "mutation { createConcept(...) { id } }"},
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

**Dependencies:** `locust`

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog

---

### 37. 📌 P2 - Environment Configuration Validator

**User Story:**
> Как DevOps engineer, я хочу валидировать конфигурацию перед стартом приложения, чтобы не получить runtime errors из-за missing env vars.

**Acceptance Criteria:**
- [ ] Pydantic models для env configuration
- [ ] Required/optional fields
- [ ] Type validation (int, bool, URL)
- [ ] Default values
- [ ] Environment-specific configs (dev/staging/prod)
- [ ] Startup validation failure если config invalid
- [ ] Config documentation auto-generation

**Implementation:**
```python
# core/config.py
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    # Database
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # Email
    SMTP_HOST: str
    SMTP_PORT: int
    FROM_EMAIL: str

    @validator('JWT_SECRET_KEY')
    def validate_jwt_secret(cls, v):
        if v == "your-super-secret-jwt-key-change-in-production":
            raise ValueError("You must change JWT_SECRET_KEY in production!")
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v

    class Config:
        env_file = ".env"

settings = Settings()  # Raises ValidationError if invalid
```

**Dependencies:** `pydantic[dotenv]`

**Estimated Effort:** 3 story points

**Status:** 📋 Backlog

---

### 38. ⚡ P1 - GraphQL Persistent Queries

**User Story:**
> Как frontend developer, я хочу использовать persisted queries, чтобы снизить размер GraphQL запросов и увеличить безопасность.

**Acceptance Criteria:**
- [ ] Query registration endpoint
- [ ] Query ID <-> Query mapping в Redis
- [ ] Client sends только query ID вместо полного query
- [ ] Automatic Persisted Queries (APQ) support
- [ ] Query whitelist режим (allow only registered queries)
- [ ] Query registry UI для админов

**Implementation:**
```python
# core/persisted_queries.py
class PersistedQueryExtension(Extension):
    async def resolve(self, _next, root, info, *args, **kwargs):
        query_id = info.context['request'].headers.get('X-Query-ID')
        if query_id:
            query = await redis_client.get(f"persisted_query:{query_id}")
            if query:
                info.context['query'] = query
        return await _next(root, info, *args, **kwargs)
```

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog

---

### 39. 💡 P3 - Audit Log Visualization Dashboard

**User Story:**
> Как admin, я хочу видеть визуализацию audit logs (timeline, charts), чтобы быстро находить подозрительную активность.

**Acceptance Criteria:**
- [ ] Web UI для просмотра логов
- [ ] Filters: user, action, date range, entity type
- [ ] Timeline view
- [ ] Charts: actions per day, top users, error rate
- [ ] Export в CSV/JSON
- [ ] Search по description
- [ ] Drill-down в детали события

**Estimated Effort:** 13 story points

**Status:** 📋 Backlog

---

### 40. 📌 P2 - GDPR Compliance Tools

**User Story:**
> Как compliance officer, я хочу иметь инструменты для GDPR compliance (data export, right to be forgotten), чтобы соответствовать законодательству.

**Acceptance Criteria:**
- [ ] User data export (JSON/CSV)
  - Все данные пользователя в одном архиве
  - Profile, audit logs, uploaded files, etc.
- [ ] Right to be forgotten:
  - Hard delete пользователя и всех связанных данных
  - Anonymization как альтернатива
- [ ] Consent management:
  - Cookie consent tracking
  - Email consent tracking
  - Data processing consent
- [ ] Data retention policies
- [ ] Data breach notification workflow
- [ ] Privacy policy version tracking

**GraphQL Mutations:**
```graphql
mutation ExportMyData {
  exportMyData {
    downloadUrl
    expiresAt
  }
}

mutation DeleteMyAccount {
  deleteMyAccount(input: {
    password: "current_password"
    reason: "No longer using"
    anonymize: false  # true для anonymization
  }) {
    success
  }
}
```

**Estimated Effort:** 13 story points

**Status:** 📋 Backlog

---

### 41. 💡 P3 - Internationalization (i18n) Framework

**User Story:**
> Как backend developer, я хочу иметь i18n framework для error messages и emails, чтобы поддерживать несколько языков.

**Acceptance Criteria:**
- [ ] Translation files (JSON/YAML)
- [ ] Language detection из:
  - `Accept-Language` header
  - User profile preference
  - Query parameter `?lang=ru`
- [ ] Translated error messages
- [ ] Translated email templates
- [ ] GraphQL queries возвращают переводы:
  ```graphql
  query GetConcept($id: ID!, $lang: String = "en") {
    concept(id: $id) {
      name(lang: $lang)
      description(lang: $lang)
    }
  }
  ```
- [ ] Fallback на default language
- [ ] Translation keys validation (no missing keys)

**Implementation:**
```python
# core/i18n.py
translations = {
    "en": {
        "error.auth.invalid_credentials": "Invalid username or password",
        "error.auth.token_expired": "Token has expired",
    },
    "ru": {
        "error.auth.invalid_credentials": "Неверное имя пользователя или пароль",
        "error.auth.token_expired": "Токен истек",
    }
}

def translate(key: str, lang: str = "en") -> str:
    return translations.get(lang, {}).get(key, translations["en"][key])
```

**Dependencies:** `python-i18n`, `babel`

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog

---

### 42. ⚡ P1 - Database Read Replicas Support

**User Story:**
> Как backend architect, я хочу поддерживать read replicas для масштабирования read-heavy workloads.

**Acceptance Criteria:**
- [ ] Multiple database connections (primary + replicas)
- [ ] Read queries автоматически идут на replicas
- [ ] Write queries идут на primary
- [ ] Fallback на primary если replica unavailable
- [ ] Replica lag monitoring
- [ ] Session-level routing (sticky sessions)

**Implementation:**
```python
# core/database.py
from sqlalchemy.orm import sessionmaker

# Primary DB (writes)
primary_engine = create_engine(PRIMARY_DATABASE_URL)
PrimarySession = sessionmaker(bind=primary_engine)

# Read replica (reads)
replica_engine = create_engine(REPLICA_DATABASE_URL)
ReplicaSession = sessionmaker(bind=replica_engine)

# Routing
class DatabaseRouter:
    def get_session(self, write: bool = False):
        if write:
            return PrimarySession()
        else:
            return ReplicaSession()

db_router = DatabaseRouter()

# Использование
def get_languages():
    db = db_router.get_session(write=False)  # Read from replica
    return db.query(Language).all()

def create_language(name: str):
    db = db_router.get_session(write=True)  # Write to primary
    ...
```

**Estimated Effort:** 13 story points

**Status:** 📋 Backlog

---

### 43. 📌 P2 - API Gateway Integration (Kong/Envoy)

**User Story:**
> Как platform engineer, я хочу интегрировать API Gateway для centralized rate limiting, auth, и monitoring.

**Acceptance Criteria:**
- [ ] Kong/Envoy configuration
- [ ] JWT validation на gateway level
- [ ] Rate limiting на gateway
- [ ] Request/response transformation
- [ ] Service mesh integration
- [ ] Canary deployments support
- [ ] Circuit breaker pattern

**Estimated Effort:** 21 story points

**Status:** 📋 Backlog

---

### 44. 💡 P3 - Event Sourcing & CQRS (опционально)

**User Story:**
> Как architect, я хочу иметь event sourcing для критических entities, чтобы иметь полную историю изменений.

**Acceptance Criteria:**
- [ ] Event store (PostgreSQL или EventStoreDB)
- [ ] Event models:
  - `UserCreatedEvent`
  - `UserUpdatedEvent`
  - `ConceptCreatedEvent`
  - etc.
- [ ] Event replay mechanism
- [ ] Read models (projections)
- [ ] Command handlers
- [ ] Event handlers
- [ ] Snapshots для performance

**Estimated Effort:** 34 story points

**Status:** 📋 Backlog

---

### 45. 📌 P2 - Service Health Dashboard

**User Story:**
> Как operations engineer, я хочу видеть dashboard со всеми метриками и health checks в одном месте.

**Acceptance Criteria:**
- [ ] Grafana dashboard setup
- [ ] Panels:
  - Request rate (req/sec)
  - Error rate (%)
  - Latency percentiles (p50, p95, p99)
  - Database connections
  - Redis memory usage
  - Celery queue length
  - Disk space
  - Memory usage
- [ ] Alerts configuration
- [ ] Historical data (30 days)

**Dependencies:** Prometheus + Grafana

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog

---

### 46. ⚡ P1 - Security Headers Middleware (App-Level)

**User Story:**
> Как security engineer, я хочу иметь security headers на app level (не только nginx), чтобы защитить API даже если nginx bypassed.

**Acceptance Criteria:**
- [ ] Headers в каждом response:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000`
  - `Content-Security-Policy`
  - `Referrer-Policy: no-referrer`
  - `Permissions-Policy`
- [ ] Configurable через env vars
- [ ] Middleware для автоматического добавления

**Implementation:**
```python
# middleware/security_headers.py
class SecurityHeadersMiddleware:
    async def __call__(self, request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response
```

**Estimated Effort:** 2 story points

**Status:** 📋 Backlog

---

### 47. 📌 P2 - Database Connection Pool Monitoring

**User Story:**
> Как DBA, я хочу мониторить connection pool (active connections, wait time), чтобы оптимизировать pool settings.

**Acceptance Criteria:**
- [ ] Metrics:
  - Active connections
  - Idle connections
  - Waiting requests
  - Connection acquisition time
  - Connection errors
- [ ] Prometheus metrics export
- [ ] Alerts при pool exhaustion
- [ ] Auto-scaling pool size (опционально)

**Implementation:**
```python
# core/database.py
from prometheus_client import Gauge

db_connections_active = Gauge('db_connections_active', 'Active DB connections')
db_connections_idle = Gauge('db_connections_idle', 'Idle DB connections')

def update_db_metrics():
    pool = engine.pool
    db_connections_active.set(pool.checkedout())
    db_connections_idle.set(pool.size() - pool.checkedout())

# Periodic task для обновления метрик
@celery_app.task
def collect_db_metrics():
    update_db_metrics()
```

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog

---

### 48. 💡 P3 - GraphQL Schema Stitching/Federation

**User Story:**
> Как microservices architect, я хочу объединить несколько GraphQL схем в одну, чтобы frontend делал запросы к одному endpoint.

**Acceptance Criteria:**
- [ ] Apollo Federation setup
- [ ] Service A (auth service)
- [ ] Service B (content service)
- [ ] Gateway для объединения схем
- [ ] Cross-service references
- [ ] Distributed queries

**Dependencies:** `strawberry-graphql[apollo-federation]`

**Estimated Effort:** 21 story points

**Status:** 📋 Backlog

---

### 49. 📌 P2 - CLI Tool для Admin Tasks

**User Story:**
> Как admin, я хочу иметь CLI tool для выполнения admin tasks (create user, reset password, run migrations).

**Acceptance Criteria:**
- [ ] Click/Typer based CLI
- [ ] Commands:
  - `python cli.py user create --username admin --role admin`
  - `python cli.py user reset-password --email user@example.com`
  - `python cli.py db migrate`
  - `python cli.py db seed`
  - `python cli.py backup create`
  - `python cli.py logs cleanup --days 90`
- [ ] Interactive prompts для sensitive operations
- [ ] Progress bars для long-running tasks
- [ ] Colorized output

**Implementation:**
```python
# cli.py
import click

@click.group()
def cli():
    """Admin CLI for МультиПУЛЬТ"""
    pass

@cli.group()
def user():
    """User management commands"""
    pass

@user.command()
@click.option('--username', required=True)
@click.option('--email', required=True)
@click.option('--role', default='user')
def create(username, email, role):
    """Create a new user"""
    click.echo(f"Creating user {username}...")
    # Logic here

if __name__ == '__main__':
    cli()
```

**Dependencies:** `click` or `typer`

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog

---

### 50. ⚡ P1 - Comprehensive Integration Tests

**User Story:**
> Как QA engineer, я хочу иметь полное покрытие integration tests для всех критических flows.

**Acceptance Criteria:**
- [ ] Test coverage >80%
- [ ] Integration tests для:
  - Auth flow (register → verify → login → refresh)
  - OAuth flow (Google, Telegram)
  - File upload → thumbnail → serve
  - CRUD operations для всех entities
  - Permissions/authorization
  - Rate limiting
  - Email sending
  - Audit logging
- [ ] Test fixtures для всех scenarios
- [ ] Parallel test execution
- [ ] CI integration с code coverage report

**Estimated Effort:** 21 story points

**Status:** 📋 Backlog

---

### 51. 📌 P2 - Docker Multi-Stage Build Optimization

**User Story:**
> Как DevOps engineer, я хочу оптимизировать Docker image size и build time.

**Acceptance Criteria:**
- [ ] Multi-stage Dockerfile
- [ ] Separate build и runtime stages
- [ ] Layer caching optimization
- [ ] Image size <200MB (сейчас ~500MB)
- [ ] Security scanning (Trivy/Snyk)
- [ ] Non-root user для runtime
- [ ] .dockerignore optimization

**Implementation:**
```dockerfile
# Dockerfile (multi-stage)
FROM python:3.11-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
RUN adduser --disabled-password --gecos '' appuser
USER appuser
CMD ["python", "app.py"]
```

**Estimated Effort:** 3 story points

**Status:** 📋 Backlog

---

### 52. 💡 P3 - A/B Testing Framework

**User Story:**
> Как product manager, я хочу проводить A/B тесты для новых фичи, чтобы измерять impact.

**Acceptance Criteria:**
- [ ] Experiment framework
- [ ] Variant assignment (A/B/C)
- [ ] Consistent assignment (same user → same variant)
- [ ] Metrics tracking
- [ ] Statistical significance calculation
- [ ] Admin UI для создания experiments
- [ ] GraphQL query: `getExperimentVariant(experimentName: String!)`

**Estimated Effort:** 21 story points

**Status:** 📋 Backlog

---

### 53. 📌 P2 - API Request/Response Logging

**User Story:**
> Как support engineer, я хочу логировать все API requests/responses для debugging customer issues.

**Acceptance Criteria:**
- [ ] Request logging:
  - Method, path, headers, body
  - User ID (if authenticated)
  - Request ID
  - Timestamp
- [ ] Response logging:
  - Status code
  - Response time
  - Body (optional, для errors)
- [ ] Configurable log level (dev: verbose, prod: errors only)
- [ ] PII filtering (passwords, tokens)
- [ ] Log retention policy
- [ ] Search by request_id

**Implementation:**
```python
# middleware/request_logging.py
import time

class RequestLoggingMiddleware:
    async def __call__(self, request, call_next):
        start_time = time.time()

        # Log request
        logger.info("Request", extra={
            'method': request.method,
            'path': request.url.path,
            'request_id': request.state.request_id,
            'user_id': getattr(request.state, 'user_id', None)
        })

        response = await call_next(request)

        # Log response
        duration = time.time() - start_time
        logger.info("Response", extra={
            'request_id': request.state.request_id,
            'status_code': response.status_code,
            'duration_ms': duration * 1000
        })

        return response
```

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog

---

### 54. ⚡ P1 - Graceful Shutdown Handling

**User Story:**
> Как platform engineer, я хочу graceful shutdown при деплое, чтобы не прерывать активные requests.

**Acceptance Criteria:**
- [ ] Signal handlers (SIGTERM, SIGINT)
- [ ] Wait for active requests to complete (timeout: 30s)
- [ ] Reject new requests во время shutdown
- [ ] Close database connections gracefully
- [ ] Close Redis connections
- [ ] Flush logs
- [ ] Health check returns 503 during shutdown

**Implementation:**
```python
# app.py
import signal
import asyncio

shutdown_event = asyncio.Event()

def shutdown_handler(signum, frame):
    logger.info("Received shutdown signal")
    shutdown_event.set()

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

# Uvicorn с graceful shutdown
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        timeout_graceful_shutdown=30
    )
```

**Estimated Effort:** 3 story points

**Status:** 📋 Backlog

---

### 55. 📌 P2 - Template Customization System

**User Story:**
> Как template user, я хочу легко кастомизировать email templates, error messages, и брендинг без изменения кода.

**Acceptance Criteria:**
- [ ] Configurable branding:
  - App name
  - Logo URL
  - Primary color
  - Email sender name
- [ ] Custom email templates (Jinja2)
- [ ] Custom error messages
- [ ] Template variables injection
- [ ] Preview mode для templates
- [ ] Version control для templates

**Implementation:**
```python
# core/branding.py
class BrandingConfig:
    def __init__(self):
        self.app_name = os.getenv('APP_NAME', 'МультиПУЛЬТ')
        self.logo_url = os.getenv('LOGO_URL', '/static/logo.png')
        self.primary_color = os.getenv('PRIMARY_COLOR', '#007bff')
        self.email_sender = os.getenv('EMAIL_SENDER', 'noreply@multipult.dev')

branding = BrandingConfig()

# В email templates
<!DOCTYPE html>
<html>
<head>
    <style>
        .header { background-color: {{ branding.primary_color }}; }
    </style>
</head>
<body>
    <div class="header">
        <img src="{{ branding.logo_url }}" alt="{{ branding.app_name }}">
    </div>
    ...
</body>
</html>
```

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog

---

## 📊 Summary

**Всего новых задач:** 40 (16-55)

**По приоритетам:**
- 🔥 P0 (Критические): 5 задач
- ⚡ P1 (Высокие): 12 задач
- 📌 P2 (Средние): 14 задач
- 💡 P3 (Низкие): 9 задач

**По категориям:**
- **Infrastructure & Monitoring:** 8 задач
- **Security:** 6 задач
- **Performance:** 6 задач
- **Developer Experience:** 8 задач
- **Production Readiness:** 7 задач
- **Advanced Features:** 5 задач

---

**Обновлено:** 2025-01-19

**Следующий Review:** Еженедельно

**Приоритет для первой итерации (Quick Wins):**
1. Error Tracking (Sentry) - #16
2. Prometheus Metrics - #17
3. Structured Logging - #19
4. Request ID Tracking - #20
5. Application Rate Limiting - #21
6. Enhanced Health Checks - #32
7. Environment Config Validator - #37
8. Security Headers Middleware - #46
9. Graceful Shutdown - #54
10. Integration Tests - #50
