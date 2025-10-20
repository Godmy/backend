# Examples

Эта директория содержит практические примеры использования различных функций МультиПУЛЬТ backend.

## Содержание

- [import_export_examples.md](import_export_examples.md) - Примеры импорта и экспорта данных в JSON, CSV, XLSX

## Как использовать примеры

1. Запустите backend:
   ```bash
   docker-compose up -d
   ```

2. Получите access token через GraphQL Playground:
   ```graphql
   mutation {
     login(input: {
       username: "admin"
       password: "Admin123!"
     }) {
       accessToken
     }
   }
   ```

3. Используйте примеры из соответствующих файлов

## Требования

- Docker и Docker Compose
- curl (для bash примеров)
- Python 3.11+ с requests (для Python примеров)
- jq (опционально, для обработки JSON в bash)

## Документация

Полная документация доступна в директории [docs/](../docs/)
