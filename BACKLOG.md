# Product Backlog - МультиПУЛЬТ

Бэклог пользовательских историй для развития проекта.

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

**Обновлено:** 2025-01-16

**Следующий Review:** Еженедельно
