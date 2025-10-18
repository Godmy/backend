# Архитектура проекта МультиПУЛЬТ

## Общая структура

Проект организован по модульному принципу, где каждый модуль отвечает за свою область функциональности.

## Основные модули

### 1. Core (Ядро)
Содержит всю базовую инфраструктуру приложения:
- `database.py` - настройка подключения к БД, создание engine и сессий
- `init_db.py` - инициализация БД (ожидание подключения, создание таблиц, импорт моделей)
- `email_service.py` - сервис для отправки email (верификация, сброс пароля)
- `redis_client.py` - клиент Redis для хранения токенов и rate limiting
- `file_storage.py` - сервис для работы с файловой системой (загрузка, thumbnails)
- `models/base.py` - BaseModel с общими полями (id, created_at, updated_at)
- `models/file.py` - модель File для хранения информации о загруженных файлах
- `models/audit_log.py` - модель AuditLog для логирования действий пользователей
- `services/file_service.py` - бизнес-логика работы с файлами
- `services/audit_service.py` - бизнес-логика аудит логирования
- `schemas/schema.py` - главная GraphQL схема, объединяющая все модули
- `schemas/file.py` - GraphQL API для работы с файлами
- `schemas/audit.py` - GraphQL API для просмотра аудит логов

### 3. Auth (Аутентификация)
Полноценный модуль для работы с пользователями и правами доступа:

```
auth/
├── models/          # Модели User, Role, Permission, Profile
├── schemas/         # GraphQL схемы для auth операций
├── services/        # Бизнес-логика (UserService, AuthService, etc.)
├── dependencies/    # Зависимости для проверки авторизации
└── utils/           # JWT, хеширование паролей
```

**Модели:**
- User - пользователи системы
- Role - роли (admin, user, etc.)
- Permission - права доступа
- Profile - профили пользователей
- OAuthConnection - связи пользователей с OAuth провайдерами

**Сервисы:**
- `AuthService` - регистрация, логин, работа с токенами
- `UserService` - CRUD операции с пользователями
- `PermissionService` - управление правами доступа
- `OAuthService` - OAuth аутентификация (Google, Telegram)
- `TokenService` - управление токенами верификации и сброса пароля

### 4. Languages (Языки и концепции)
Модуль для работы с многоязычными данными:

```
languages/
├── models/          # Модели Language, Concept, Dictionary
├── schemas/         # GraphQL схемы для languages операций
└── services/        # Бизнес-логика (LanguageService, etc.)
```

**Модели:**
- `LanguageModel` - языки (ru, en, etc.)
- `ConceptModel` - иерархическая структура концепций
- `DictionaryModel` - связь концепции с языком (переводы)

**Сервисы:**
- `LanguageService` - управление языками
- `ConceptService` - работа с иерархией концепций
- `DictionaryService` - управление переводами

## Принципы организации

### Модульная структура

**core/** - базовая инфраструктура:
```
core/
├── models/              # Базовые SQLAlchemy модели
│   ├── base.py          # BaseModel для всех моделей
│   ├── file.py          # Модель File (загруженные файлы)
│   └── audit_log.py     # Модель AuditLog (логирование действий)
├── services/            # Бизнес-логика core модуля
│   ├── file_service.py  # Работа с файлами
│   └── audit_service.py # Аудит логирование
├── schemas/             # GraphQL схемы
│   ├── schema.py        # Главная схема (объединение всех модулей)
│   ├── file.py          # API для файлов
│   └── audit.py         # API для аудит логов
├── database.py          # Подключение к БД
├── init_db.py           # Инициализация БД и создание таблиц
├── email_service.py     # Сервис отправки email
├── redis_client.py      # Клиент Redis
└── file_storage.py      # Работа с файловой системой
```

**Каждый бизнес-модуль** (auth, languages, etc.):
```
module/
├── models/          # SQLAlchemy модели модуля
├── schemas/         # GraphQL схемы (типы, запросы, мутации)
└── services/        # Бизнес-логика модуля
```

### Разделение ответственности

1. **Models** (Модели):
   - Определяют структуру данных в БД
   - Содержат связи между таблицами
   - Не содержат бизнес-логику

2. **Services** (Сервисы):
   - Содержат всю бизнес-логику
   - Выполняют валидацию данных
   - Работают с базой данных через SQLAlchemy
   - Независимы от GraphQL

3. **Schemas** (Схемы):
   - Определяют GraphQL API
   - Вызывают сервисы для выполнения операций
   - Преобразуют данные в GraphQL типы
   - Обрабатывают ошибки

### Преимущества такой архитектуры

1. **Чистая структура кода**
   - Легко найти нужный файл
   - Понятная организация

2. **Переиспользование кода**
   - Сервисы можно использовать из разных мест
   - Не привязаны к GraphQL

3. **Легкое тестирование**
   - Можно тестировать сервисы независимо от API
   - Можно тестировать API с моками сервисов

4. **Масштабируемость**
   - Легко добавлять новые модули
   - Модули не зависят друг от друга

## Поток данных

### Запрос к API
```
GraphQL запрос
    ↓
Schemas (валидация, парсинг)
    ↓
Services (бизнес-логика)
    ↓
Models (база данных)
    ↓
Services (форматирование)
    ↓
Schemas (возврат результата)
    ↓
GraphQL ответ
```

### Пример: Создание языка

1. Клиент отправляет mutation:
```graphql
mutation {
  createLanguage(input: {code: "ru", name: "Russian"}) {
    id
    code
    name
  }
}
```

2. `LanguageMutation.create_language()` получает запрос
3. Создается `LanguageService` с сессией БД
4. Вызывается `service.create(code="ru", name="Russian")`
5. Сервис проверяет уникальность кода
6. Создается `LanguageModel` и сохраняется в БД
7. Результат возвращается через GraphQL

## База данных

### Миграции
- Используется Alembic для версионирования схемы БД
- Миграции хранятся в `alembic/versions/`
- Автогенерация миграций: `alembic revision --autogenerate`

### Связи между моделями

```
Language ←─┐
           │
           ├── Dictionary
           │
Concept ←──┘

User ──→ Role ──→ Permission
  │
  ├──→ Profile ──→ File (avatar)
  │
  ├──→ File (uploaded_files)
  │
  └──→ AuditLog (activity logs)
```

## Тестирование

### Структура тестов
```
tests/
├── conftest.py          # Фикстуры pytest
├── test_app.py          # Интеграционные тесты API
├── test_language.py     # Тесты модуля languages
└── test_auth.py         # Тесты модуля auth
```

### Типы тестов
1. **Unit тесты** - тестируют сервисы изолированно
2. **Integration тесты** - тестируют API endpoints
3. **E2E тесты** - тестируют полный поток

## CI/CD

### GitHub Actions
- Автоматический запуск тестов при push
- Проверка качества кода (flake8, black, mypy)
- Сборка Docker образа

### Pre-commit хуки
- Форматирование кода (black, isort)
- Проверка синтаксиса
- Проверка типов

## Развертывание

### Development
```bash
docker-compose -f docker-compose.dev.yml up
```
- Включен hot-reload
- Монтируется код проекта

### Production
```bash
docker-compose up -d
```
- Оптимизированная сборка
- Без hot-reload
- Volumes только для данных

## Расширение проекта

### Добавление нового модуля

1. Создайте структуру:
```bash
mkdir -p my_module/{models,schemas,services}
```

2. Создайте модели в `my_module/models/`
3. Создайте сервисы в `my_module/services/`
4. Создайте GraphQL схемы в `my_module/schemas/`
5. Добавьте схемы в `schemas/schema.py`
6. Импортируйте модели в `app.py` для создания таблиц

### Пример нового модуля

См. существующие модули `auth/` и `languages/` как референс.
