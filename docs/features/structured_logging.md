# Structured Logging (JSON Format)

**Status:** ✅ Implemented | **Priority:** P0 | **User Story:** #19

## Обзор

Система структурированного логирования предоставляет JSON-форматированные логи для легкого парсинга и анализа в ELK Stack, CloudWatch, Grafana Loki и других системах мониторинга.

## Основные возможности

### ✅ Реализованные функции

- **JSON-формат логов** - Все логи выводятся в JSON-формате для легкого парсинга
- **Контекстные поля** - Автоматическое добавление: timestamp, level, message, request_id, user_id, endpoint, module, function, line
- **Correlation ID** - Уникальный request_id для трассировки запросов через весь стек
- **Log Levels** - Поддержка всех уровней: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Rotation** - Автоматическая ротация по размеру и времени
- **Раздельные логи** - access.log, error.log, app.log
- **ELK/CloudWatch совместимость** - Формат логов совместим с популярными системами мониторинга

### 📍 Критические места с логированием

1. **Аутентификация** (`auth/services/auth_service.py`)
   - Попытки регистрации и логина
   - Успешные/неудачные аутентификации
   - Обновление токенов

2. **JWT Токены** (`auth/utils/jwt_handler.py`)
   - Верификация токенов
   - Ошибки валидации (expired, invalid)

3. **База данных** (`core/database.py`)
   - Подключение к БД
   - Ошибки сессий
   - Rollback операций

4. **GraphQL операции** (`core/graphql_extensions.py`)
   - Начало и завершение операций
   - Управление DB сессиями

5. **HTTP запросы** (`core/middleware/request_logging.py`)
   - Все входящие запросы
   - Коды ответов
   - Длительность запросов

## Где смотреть логи

### 1. Docker Logs (Production & Development)

**Рекомендуемый способ для Docker окружения:**

```bash
# Просмотр логов backend контейнера
docker logs humans_ontology_backend

# Следить за логами в реальном времени
docker logs -f humans_ontology_backend

# Показать последние 100 строк
docker logs --tail 100 humans_ontology_backend

# Показать логи за последний час
docker logs --since 1h humans_ontology_backend

# Фильтровать логи по уровню (через jq)
docker logs humans_ontology_backend 2>&1 | jq 'select(.level == "ERROR")'

# Фильтровать логи по event
docker logs humans_ontology_backend 2>&1 | jq 'select(.event == "user_logged_in")'

# Фильтровать логи по user_id
docker logs humans_ontology_backend 2>&1 | jq 'select(.user_id == 1)'

# Фильтровать логи по request_id (трассировка запроса)
docker logs humans_ontology_backend 2>&1 | jq 'select(.request_id == "abc12345")'
```

### 2. Файловые логи (опционально)

По умолчанию **отключено** в Docker окружении (логи идут в stdout/stderr).

Для включения установите в `.env`:
```env
LOG_FILE_ENABLED=true
LOG_DIR=logs
```

После включения логи будут записываться в:
- `logs/app.log` - Все логи (DEBUG и выше)
- `logs/access.log` - HTTP запросы (INFO уровень)
- `logs/error.log` - Ошибки и предупреждения (WARNING и выше)

### 3. Grafana Loki (Cloud/Production)

Если используете Grafana Loki для централизованного логирования:

```logql
# Все логи приложения
{container="humans_ontology_backend"}

# Только ошибки
{container="humans_ontology_backend"} |= "ERROR"

# Логи конкретного пользователя
{container="humans_ontology_backend"} | json | user_id="123"

# Попытки логина
{container="humans_ontology_backend"} | json | event="user_login_attempt"

# Неудачные логины
{container="humans_ontology_backend"} | json | event="user_login_failed"

# Трассировка запроса по request_id
{container="humans_ontology_backend"} | json | request_id="abc12345"
```

### 4. AWS CloudWatch (AWS Deployment)

Если приложение развернуто в AWS с CloudWatch:

```bash
# Через AWS CLI
aws logs tail /ecs/humans-ontology-backend --follow

# Фильтровать по уровню
aws logs filter-log-events \
  --log-group-name /ecs/humans-ontology-backend \
  --filter-pattern '{ $.level = "ERROR" }'

# Фильтровать по event
aws logs filter-log-events \
  --log-group-name /ecs/humans-ontology-backend \
  --filter-pattern '{ $.event = "user_logged_in" }'
```

### 5. ELK Stack (Elasticsearch + Kibana)

Если используете ELK Stack:

**Kibana Query:**
```
# Все логи
container.name: "humans_ontology_backend"

# Только ошибки
container.name: "humans_ontology_backend" AND level: "ERROR"

# Конкретный пользователь
container.name: "humans_ontology_backend" AND user_id: 123

# Поиск по событию
container.name: "humans_ontology_backend" AND event: "user_login_failed"

# Трассировка по request_id
container.name: "humans_ontology_backend" AND request_id: "abc12345"
```

## Примеры использования в коде

### Базовое логирование

```python
from core.structured_logging import get_logger

logger = get_logger(__name__)

# Простой лог
logger.info("User action completed")

# Лог с дополнительными полями
logger.info(
    "User registered",
    extra={
        "user_id": 123,
        "username": "john_doe",
        "event": "user_registered"
    }
)

# Лог ошибки
logger.error(
    "Database connection failed",
    extra={
        "error": str(e),
        "event": "db_connection_error"
    },
    exc_info=True  # Добавить traceback
)
```

### Логирование API запросов

```python
from core.structured_logging import log_api_request

log_api_request(
    method="POST",
    path="/api/users",
    status_code=201,
    duration_ms=125,
    user_id=42
)
```

### Логирование бизнес-событий

```python
from core.structured_logging import log_business_event

log_business_event(
    event="file_uploaded",
    user_id=123,
    file_size=1024000,
    file_type="image/png"
)
```

## Формат JSON логов

Пример JSON лога:

```json
{
  "timestamp": "2025-01-15T10:30:45.123456+00:00",
  "level": "INFO",
  "logger": "auth.services.auth_service",
  "module": "auth_service",
  "function": "login_user",
  "line": 76,
  "message": "User logged in successfully",
  "request_id": "abc12345",
  "user_id": 42,
  "username": "john_doe",
  "event": "user_logged_in"
}
```

## Важные события для мониторинга

### Аутентификация
- `user_registration_attempt` - Попытка регистрации
- `user_registration_failed` - Неудачная регистрация
- `user_registered` - Успешная регистрация
- `user_login_attempt` - Попытка логина
- `user_login_failed` - Неудачный логин (важно для безопасности!)
- `user_logged_in` - Успешный логин
- `token_refresh_attempt` - Попытка обновления токена
- `token_refresh_failed` - Неудачное обновление токена
- `token_refreshed` - Успешное обновление токена

### База данных
- `db_session_error` - Ошибка DB сессии
- `graphql_session_close_error` - Ошибка закрытия GraphQL сессии

### GraphQL
- `graphql_operation_start` - Начало GraphQL операции
- `graphql_operation_end` - Завершение GraphQL операции

## Конфигурация

### Переменные окружения

```env
# Уровень логирования
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Директория для логов
LOG_DIR=logs

# Формат логов
LOG_FORMAT=json  # json или text

# Файловое логирование (отключено по умолчанию в Docker)
LOG_FILE_ENABLED=false

# Ротация логов
LOG_ROTATION_SIZE_MB=10  # Размер файла до ротации
LOG_ROTATION_BACKUP_COUNT=5  # Количество backup файлов
```

### Настройка в коде

```python
from core.structured_logging import setup_logging

# Настроить при запуске приложения
setup_logging(
    log_level="INFO",
    log_dir="logs",
    use_json=True,
    rotation_size=10 * 1024 * 1024,  # 10MB
    rotation_backup_count=5
)
```

## Best Practices

### 1. Используйте event поля

Всегда добавляйте поле `event` для важных событий:

```python
logger.info(
    "Important business event",
    extra={"event": "payment_processed", "amount": 100.0}
)
```

### 2. Добавляйте контекст

Включайте user_id, request_id и другие контекстные данные:

```python
logger.error(
    "Operation failed",
    extra={
        "user_id": user.id,
        "operation": "file_upload",
        "error": str(e)
    },
    exc_info=True
)
```

### 3. Не логируйте чувствительные данные

**Никогда не логируйте:**
- Пароли
- Токены
- API ключи
- Персональные данные (email в DEBUG режиме можно)

### 4. Используйте правильные уровни

- `DEBUG` - Детальная отладочная информация (только для разработки)
- `INFO` - Важные события в нормальном потоке (логин, регистрация)
- `WARNING` - Предупреждения (неудачные попытки логина, устаревшие токены)
- `ERROR` - Ошибки, требующие внимания (DB errors, API failures)
- `CRITICAL` - Критические ошибки, требующие немедленного действия

### 5. Используйте exc_info для ошибок

Всегда используйте `exc_info=True` для логирования исключений:

```python
try:
    # some operation
except Exception as e:
    logger.error(
        "Operation failed",
        extra={"error": str(e)},
        exc_info=True  # Добавит полный traceback
    )
```

## Мониторинг и алерты

### Критические события для алертов

Настройте алерты в вашей системе мониторинга на следующие события:

1. **Частые неудачные логины** (потенциальная атака)
   ```
   level="WARNING" AND event="user_login_failed"
   ```

2. **Ошибки базы данных**
   ```
   level="ERROR" AND event="db_session_error"
   ```

3. **Критические ошибки**
   ```
   level="CRITICAL"
   ```

4. **Медленные запросы** (> 1 секунда)
   ```
   duration_ms > 1000
   ```

## Troubleshooting

### Логи не отображаются

1. Проверьте уровень логирования:
   ```bash
   docker exec humans_ontology_backend env | grep LOG_LEVEL
   ```

2. Проверьте, что приложение запущено:
   ```bash
   docker ps | grep backend
   ```

3. Проверьте логи контейнера:
   ```bash
   docker logs humans_ontology_backend
   ```

### Логи не в JSON формате

Проверьте переменную окружения:
```bash
docker exec humans_ontology_backend env | grep LOG_FORMAT
```

Должно быть `LOG_FORMAT=json`

### Нет request_id в логах

Request ID добавляется автоматически middleware. Проверьте, что:
1. Запрос проходит через middleware
2. Логи выполняются в контексте HTTP запроса

## См. также

- [Request Logging](request_logging.md) - HTTP Request/Response логирование
- [Request Tracing](request_tracing.md) - Распределенная трассировка
- [Sentry Integration](sentry.md) - Error tracking
- [Prometheus Metrics](prometheus.md) - Метрики приложения

---

**Implemented in:** `core/structured_logging.py`
**Used in:** All critical services (auth, database, GraphQL)
**Configuration:** `.env` файл или environment variables
