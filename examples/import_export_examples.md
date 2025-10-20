# Import/Export Examples

Практические примеры использования системы импорта/экспорта.

## Экспорт данных

### Экспорт всех концепций в JSON

**GraphQL:**
```graphql
mutation ExportAllConcepts {
  exportData(
    entityType: CONCEPTS
    format: JSON
  ) {
    jobId
    url
    expiresAt
    status
  }
}
```

**Response:**
```json
{
  "data": {
    "exportData": {
      "jobId": 1,
      "url": "/exports/concepts_20250120_153045.json",
      "expiresAt": 1737471045,
      "status": "COMPLETED"
    }
  }
}
```

**Скачивание файла:**
```bash
curl http://localhost:8000/exports/concepts_20250120_153045.json -o concepts.json
```

### Экспорт концепций на русском языке в XLSX

```graphql
mutation ExportRussianConcepts {
  exportData(
    entityType: CONCEPTS
    format: XLSX
    filters: { language: "ru" }
  ) {
    url
    expiresAt
  }
}
```

### Экспорт всех языков в CSV

```graphql
mutation ExportLanguages {
  exportData(
    entityType: LANGUAGES
    format: CSV
  ) {
    url
  }
}
```

### Экспорт словарей

```graphql
mutation ExportDictionaries {
  exportData(
    entityType: DICTIONARIES
    format: JSON
    filters: { language: "en" }
  ) {
    jobId
    url
  }
}
```

## Импорт данных

### Импорт языков из JSON

**Prepare file (languages.json):**
```json
[
  {
    "code": "fr",
    "name": "French",
    "native_name": "Français",
    "rtl": false
  },
  {
    "code": "de",
    "name": "German",
    "native_name": "Deutsch",
    "rtl": false
  }
]
```

**GraphQL mutation:**
```graphql
mutation ImportLanguages($file: Upload!) {
  importData(
    file: $file
    entityType: LANGUAGES
  ) {
    jobId
    status
    message
  }
}
```

**Variables:**
```json
{
  "file": null
}
```

**cURL example:**
```bash
curl -X POST http://localhost:8000/graphql \
  -F 'operations={"query":"mutation ImportLanguages($file: Upload!) { importData(file: $file, entityType: LANGUAGES) { jobId status message } }","variables":{"file":null}}' \
  -F 'map={"0":["variables.file"]}' \
  -F '0=@languages.json'
```

### Импорт концепций с обновлением существующих

**Prepare file (concepts.json):**
```json
[
  {
    "path": "/user",
    "depth": 0,
    "translations": [
      {
        "language_code": "en",
        "name": "User",
        "description": "A person who uses the system"
      },
      {
        "language_code": "ru",
        "name": "Пользователь",
        "description": "Человек, использующий систему"
      }
    ]
  },
  {
    "path": "/admin",
    "depth": 0,
    "translations": [
      {
        "language_code": "en",
        "name": "Administrator",
        "description": "System administrator"
      }
    ]
  }
]
```

**GraphQL:**
```graphql
mutation ImportConceptsUpdate($file: Upload!) {
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

### Валидация данных перед импортом (dry run)

```graphql
mutation ValidateData($file: Upload!) {
  importData(
    file: $file
    entityType: CONCEPTS
    options: {
      validateOnly: true
    }
  ) {
    jobId
    status
    message
  }
}
```

Затем проверяем результаты:
```graphql
query CheckValidation {
  importJob(jobId: 1) {
    status
    totalCount
    processedCount
    errorCount
    errors
  }
}
```

### Импорт с пропуском дубликатов

```graphql
mutation ImportSkipDuplicates($file: Upload!) {
  importData(
    file: $file
    entityType: LANGUAGES
    options: {
      onDuplicate: SKIP
    }
  ) {
    jobId
    message
  }
}
```

### Импорт с ошибкой при дубликатах

```graphql
mutation ImportFailOnDuplicate($file: Upload!) {
  importData(
    file: $file
    entityType: LANGUAGES
    options: {
      onDuplicate: FAIL
    }
  ) {
    jobId
    status
    message
  }
}
```

## Мониторинг заданий

### Проверка статуса конкретного задания

```graphql
query JobStatus {
  importJob(jobId: 1) {
    id
    jobType
    entityType
    status
    format
    totalCount
    processedCount
    errorCount
    progressPercent
    errors
    errorMessage
    fileUrl
    expiresAt
    createdAt
    updatedAt
  }
}
```

### Список всех моих заданий

```graphql
query MyJobs {
  myImportExportJobs(limit: 20, offset: 0) {
    id
    jobType
    entityType
    status
    format
    totalCount
    processedCount
    errorCount
    progressPercent
    fileUrl
    createdAt
  }
}
```

### Фильтрация заданий по типу

```graphql
query MyExportJobs {
  myImportExportJobs(jobType: "export", limit: 10) {
    id
    entityType
    status
    fileUrl
    expiresAt
    createdAt
  }
}
```

## Обработка ошибок

### Пример ответа с ошибками

**Request:**
```graphql
mutation ImportWithErrors($file: Upload!) {
  importData(
    file: $file
    entityType: LANGUAGES
  ) {
    jobId
    status
    message
  }
}
```

**Response:**
```json
{
  "data": {
    "importData": {
      "jobId": 5,
      "status": "FAILED",
      "message": "Import failed: 2 errors occurred"
    }
  }
}
```

**Checking errors:**
```graphql
query CheckErrors {
  importJob(jobId: 5) {
    errorCount
    errors
  }
}
```

**Response:**
```json
{
  "data": {
    "importJob": {
      "errorCount": 2,
      "errors": "[{\"row\": 3, \"message\": \"Missing required field: name\"}, {\"row\": 5, \"message\": \"Duplicate code: en\"}]"
    }
  }
}
```

## Python примеры

### Экспорт с использованием requests

```python
import requests
import json

# GraphQL endpoint
url = "http://localhost:8000/graphql"

# Authorization header (получите токен через login mutation)
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    "Content-Type": "application/json"
}

# Export mutation
query = """
mutation ExportConcepts {
  exportData(
    entityType: CONCEPTS
    format: JSON
  ) {
    url
    expiresAt
  }
}
"""

response = requests.post(url, json={"query": query}, headers=headers)
data = response.json()

# Get download URL
download_url = data["data"]["exportData"]["url"]
print(f"Download URL: http://localhost:8000{download_url}")

# Download file
file_response = requests.get(f"http://localhost:8000{download_url}")
with open("concepts_export.json", "wb") as f:
    f.write(file_response.content)
```

### Импорт с использованием requests

```python
import requests

url = "http://localhost:8000/graphql"
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}

# Prepare multipart request
operations = {
    "query": """
        mutation ImportLanguages($file: Upload!) {
            importData(file: $file, entityType: LANGUAGES) {
                jobId
                status
                message
            }
        }
    """,
    "variables": {"file": None}
}

map_data = {"0": ["variables.file"]}

files = {
    "operations": (None, json.dumps(operations), "application/json"),
    "map": (None, json.dumps(map_data), "application/json"),
    "0": ("languages.json", open("languages.json", "rb"), "application/json")
}

response = requests.post(url, files=files, headers=headers)
result = response.json()

print(f"Job ID: {result['data']['importData']['jobId']}")
print(f"Status: {result['data']['importData']['status']}")
print(f"Message: {result['data']['importData']['message']}")
```

## Автоматизация

### Bash скрипт для регулярного экспорта

```bash
#!/bin/bash

# Configuration
API_URL="http://localhost:8000/graphql"
TOKEN="YOUR_ACCESS_TOKEN"
BACKUP_DIR="./backups"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Export concepts
echo "Exporting concepts..."
RESULT=$(curl -s -X POST "$API_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { exportData(entityType: CONCEPTS, format: JSON) { url } }"}')

# Extract URL
EXPORT_URL=$(echo $RESULT | jq -r '.data.exportData.url')

# Download file
if [ "$EXPORT_URL" != "null" ]; then
  curl -s "http://localhost:8000$EXPORT_URL" -o "$BACKUP_DIR/concepts_$(date +%Y%m%d).json"
  echo "✓ Concepts exported successfully"
else
  echo "✗ Export failed"
fi
```

### Cron job для автоматических бэкапов

```bash
# Ежедневный экспорт в 3:00 AM
0 3 * * * /path/to/export_script.sh >> /var/log/export.log 2>&1
```

## Миграция данных между окружениями

### 1. Экспорт из production

```bash
# Export from production
curl -X POST https://prod-api.example.com/graphql \
  -H "Authorization: Bearer $PROD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { exportData(entityType: CONCEPTS, format: JSON) { url } }"}' \
  | jq -r '.data.exportData.url' \
  | xargs -I {} curl "https://prod-api.example.com{}" -o concepts_prod.json
```

### 2. Импорт в staging

```bash
# Import to staging
curl -X POST http://staging-api.example.com/graphql \
  -H "Authorization: Bearer $STAGING_TOKEN" \
  -F 'operations={"query":"mutation ImportConcepts($file: Upload!) { importData(file: $file, entityType: CONCEPTS, options: { onDuplicate: UPDATE }) { message } }","variables":{"file":null}}' \
  -F 'map={"0":["variables.file"]}' \
  -F '0=@concepts_prod.json'
```

## Советы и лучшие практики

1. **Всегда используйте валидацию перед импортом больших файлов:**
   ```graphql
   options: { validateOnly: true }
   ```

2. **Для миграций используйте стратегию UPDATE:**
   ```graphql
   options: { onDuplicate: UPDATE }
   ```

3. **Регулярно проверяйте статус заданий:**
   ```graphql
   query { myImportExportJobs { status errorCount } }
   ```

4. **Скачивайте экспортированные файлы сразу** (срок действия 24 часа)

5. **Для больших объемов данных разбивайте файлы на части**

6. **Сохраняйте резервные копии перед импортом с UPDATE или FAIL**
