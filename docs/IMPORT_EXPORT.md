# Import/Export System Documentation

Система импорта и экспорта данных позволяет выгружать и загружать данные в различных форматах (JSON, CSV, XLSX).

## Возможности

### Экспорт
- Экспорт концепций, словарей, пользователей, языков
- Форматы: JSON, CSV, XLSX
- Фильтрация данных (по языку, датам)
- Автоматическая очистка старых файлов (24 часа)
- Отслеживание статуса задания

### Импорт
- Импорт из JSON, CSV, XLSX
- Валидация данных перед сохранением
- Стратегии обработки дубликатов: skip, update, fail
- Режим валидации (без сохранения в БД)
- Детальный отчет об ошибках

## GraphQL API

### Экспорт данных

**Mutation:**
```graphql
mutation ExportConcepts {
  exportData(
    entityType: CONCEPTS
    format: JSON
    filters: { language: "en" }
  ) {
    jobId
    url
    expiresAt
    status
  }
}
```

**Параметры:**
- `entityType`: Тип сущности (`CONCEPTS`, `DICTIONARIES`, `USERS`, `LANGUAGES`)
- `format`: Формат экспорта (`JSON`, `CSV`, `XLSX`)
- `filters` (опционально): Фильтры для экспорта
  - `language`: Код языка для фильтрации
  - `dateFrom`: Дата начала (ISO 8601)
  - `dateTo`: Дата окончания (ISO 8601)

**Response:**
- `jobId`: ID задания
- `url`: URL для скачивания файла (например, `/exports/concepts_20250120_153045.json`)
- `expiresAt`: Timestamp истечения ссылки (UTC)
- `status`: Статус (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`)

### Импорт данных

**Mutation:**
```graphql
mutation ImportConcepts($file: Upload!) {
  importData(
    file: $file
    entityType: CONCEPTS
    options: {
      onDuplicate: UPDATE
      validateOnly: false
    }
  ) {
    jobId
    status
    message
  }
}
```

**Параметры:**
- `file`: Файл для загрузки (multipart/form-data)
- `entityType`: Тип сущности
- `options` (опционально):
  - `onDuplicate`: Стратегия обработки дубликатов (`SKIP`, `UPDATE`, `FAIL`)
  - `validateOnly`: Только валидация без сохранения (default: `false`)

**Response:**
- `jobId`: ID задания
- `status`: Статус выполнения
- `message`: Сообщение о результате

### Проверка статуса задания

**Query:**
```graphql
query ImportJobStatus {
  importJob(jobId: 123) {
    id
    jobType
    entityType
    status
    totalCount
    processedCount
    errorCount
    errors
    progressPercent
    fileUrl
    expiresAt
    createdAt
  }
}
```

### Список моих заданий

**Query:**
```graphql
query MyJobs {
  myImportExportJobs(jobType: "export", limit: 10, offset: 0) {
    id
    jobType
    entityType
    status
    format
    totalCount
    processedCount
    progressPercent
    fileUrl
    createdAt
  }
}
```

## Форматы данных

### Концепции (Concepts)

**JSON:**
```json
[
  {
    "id": 1,
    "parent_id": null,
    "path": "/user",
    "depth": 0,
    "created_at": "2025-01-20T10:00:00",
    "updated_at": "2025-01-20T10:00:00",
    "translations": [
      {
        "language_code": "en",
        "language_name": "English",
        "name": "User",
        "description": "A person who uses the system",
        "image": null
      },
      {
        "language_code": "ru",
        "language_name": "Russian",
        "name": "Пользователь",
        "description": "Человек, использующий систему",
        "image": null
      }
    ]
  }
]
```

**CSV/XLSX:**
Вложенные структуры (translations) сохраняются как JSON-строки.

### Словари (Dictionaries)

**JSON:**
```json
[
  {
    "id": 1,
    "concept_id": 1,
    "concept_path": "/user",
    "language_id": 1,
    "language_code": "en",
    "language_name": "English",
    "name": "User",
    "description": "A person who uses the system",
    "image": null,
    "created_at": "2025-01-20T10:00:00",
    "updated_at": "2025-01-20T10:00:00"
  }
]
```

### Пользователи (Users)

**JSON:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_active": true,
    "is_verified": true,
    "created_at": "2025-01-20T10:00:00",
    "updated_at": "2025-01-20T10:00:00",
    "roles": ["admin", "user"],
    "profile": {
      "first_name": "Admin",
      "last_name": "User",
      "bio": "System administrator"
    }
  }
]
```

**Важно:** Пароли **не экспортируются** по соображениям безопасности. При импорте пользователей устанавливается временный пароль `ChangeMe123!`.

### Языки (Languages)

**JSON:**
```json
[
  {
    "id": 1,
    "code": "en",
    "name": "English",
    "native_name": "English",
    "rtl": false,
    "created_at": "2025-01-20T10:00:00",
    "updated_at": "2025-01-20T10:00:00"
  }
]
```

## Стратегии обработки дубликатов

### SKIP (по умолчанию)
Пропускает существующие записи, импортирует только новые.

**Пример:**
```graphql
mutation {
  importData(
    file: $file
    entityType: LANGUAGES
    options: { onDuplicate: SKIP }
  ) {
    message
  }
}
```

### UPDATE
Обновляет существующие записи новыми данными.

**Пример:**
```graphql
mutation {
  importData(
    file: $file
    entityType: LANGUAGES
    options: { onDuplicate: UPDATE }
  ) {
    message
  }
}
```

### FAIL
Возвращает ошибку при обнаружении дубликата.

**Пример:**
```graphql
mutation {
  importData(
    file: $file
    entityType: LANGUAGES
    options: { onDuplicate: FAIL }
  ) {
    message
  }
}
```

## Режим валидации

Проверяет данные без фактического сохранения в базу данных.

**Пример:**
```graphql
mutation {
  importData(
    file: $file
    entityType: CONCEPTS
    options: { validateOnly: true }
  ) {
    jobId
    status
    message
  }
}
```

После валидации можно проверить результат:
```graphql
query {
  importJob(jobId: 123) {
    processedCount  # Количество валидных записей
    errorCount      # Количество ошибок
    errors          # Детали ошибок
  }
}
```

## Обработка ошибок

При импорте система отслеживает ошибки для каждой строки:

**Пример response с ошибками:**
```json
{
  "data": {
    "importJob": {
      "errorCount": 2,
      "errors": "[{\"row\": 5, \"message\": \"Missing required field: name\"}, {\"row\": 12, \"message\": \"Duplicate code: en\"}]"
    }
  }
}
```

## Скачивание экспортированных файлов

После успешного экспорта файл доступен по URL:

```
GET http://localhost:8000/exports/concepts_20250120_153045.json
```

**Важно:**
- Файлы автоматически удаляются через 24 часа
- URL содержит timestamp для уникальности
- Путь защищен от path traversal атак

## Права доступа

### Экспорт
- **Concepts, Dictionaries, Languages**: Доступно всем аутентифицированным пользователям
- **Users**: Только администраторы

### Импорт
- **Concepts, Dictionaries, Languages**: Доступно всем аутентифицированным пользователям
- **Users**: Только администраторы

## Примеры использования

### Экспорт всех концепций в JSON
```graphql
mutation {
  exportData(entityType: CONCEPTS, format: JSON) {
    url
    expiresAt
  }
}
```

### Экспорт концепций на русском языке в XLSX
```graphql
mutation {
  exportData(
    entityType: CONCEPTS
    format: XLSX
    filters: { language: "ru" }
  ) {
    url
  }
}
```

### Импорт концепций с обновлением существующих
```graphql
mutation ImportConcepts($file: Upload!) {
  importData(
    file: $file
    entityType: CONCEPTS
    options: { onDuplicate: UPDATE }
  ) {
    jobId
    message
  }
}
```

### Валидация данных перед импортом
```graphql
mutation ValidateData($file: Upload!) {
  importData(
    file: $file
    entityType: LANGUAGES
    options: { validateOnly: true }
  ) {
    jobId
    status
  }
}
```

Затем проверка результатов:
```graphql
query {
  importJob(jobId: 123) {
    processedCount
    errorCount
    errors
  }
}
```

## Ограничения

- Максимальный размер импортируемого файла: зависит от настроек сервера (по умолчанию без ограничений)
- Экспортированные файлы хранятся 24 часа
- Импорт/экспорт выполняется синхронно (для больших объемов рекомендуется использовать Celery)
- При импорте пользователей пароли не импортируются (устанавливается временный)

## Конфигурация

### Переменные окружения

```bash
# Директория для экспортированных файлов
EXPORT_DIR=exports

# Автоматическая очистка старых файлов (часы)
# Настраивается в Celery задаче
```

### Автоматическая очистка

Для настройки автоматической очистки старых экспортов добавьте Celery задачу:

```python
# tasks/cleanup_tasks.py
from core.services.export_service import ExportService

@celery_app.task
def cleanup_old_exports():
    db = next(get_db())
    export_service = ExportService(db)
    deleted = export_service.cleanup_old_exports(hours=24)
    logger.info(f"Cleaned up {deleted} old export files")
```

Schedule в Celery Beat:
```python
celery_app.conf.beat_schedule = {
    'cleanup-exports-daily': {
        'task': 'tasks.cleanup_tasks.cleanup_old_exports',
        'schedule': crontab(hour=3, minute=0),  # Каждый день в 3:00
    },
}
```

## Производительность

### Оптимизация экспорта
- Используйте фильтры для уменьшения объема данных
- Для больших объемов предпочтительнее CSV (быстрее чем XLSX)
- JSON - наиболее универсальный формат, сохраняет вложенные структуры

### Оптимизация импорта
- Используйте `validateOnly` для проверки перед реальным импортом
- Для больших файлов разбивайте на меньшие части
- Используйте стратегию `SKIP` для ускорения повторного импорта

## Безопасность

- Все операции требуют аутентификации
- Импорт/экспорт пользователей - только для администраторов
- Пароли не экспортируются
- Защита от path traversal атак при скачивании файлов
- Валидация данных перед импортом
- Автоматическая очистка временных файлов

## Поддержка

Для вопросов и предложений создавайте issue в репозитории проекта.
