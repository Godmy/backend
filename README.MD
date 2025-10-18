# МультиПУЛЬТ (Multipult)

Современный backend на Python с GraphQL API для управления шаблонами и контентом.

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

**📝 Последние изменения:** [CHANGELOG.md](CHANGELOG.md) | **📋 Планы:** [BACKLOG.md](BACKLOG.md) | **📚 Документация:** [DOCS_STRUCTURE.md](DOCS_STRUCTURE.md)

## Технологии

- **Python 3.11+** - Основной язык разработки
- **FastAPI/Starlette** - Асинхронный веб-фреймворк
- **Strawberry GraphQL** - GraphQL сервер для Python
- **SQLAlchemy** - ORM для работы с базой данных
- **PostgreSQL** - Реляционная база данных
- **Redis** - Кэширование и хранение токенов
- **Alembic** - Миграции базы данных
- **Docker & Docker Compose** - Контейнеризация
- **JWT** - Аутентификация и авторизация
- **Pillow** - Обработка изображений и создание thumbnails
- **Nginx** - Reverse proxy (production)
- **MailPit** - Email тестирование (development)

## Возможности

- **GraphQL API** с автоматической генерацией схемы
- **Система аутентификации** с JWT токенами (access + refresh)
- **OAuth 2.0** - вход через Google и Telegram
- **Email верификация** с отправкой писем и токенами
- **Сброс пароля** через email
- **Управление пользователями**, ролями и правами доступа
- **File Upload System** - загрузка файлов с автоматическим созданием thumbnails
- **Audit Logging** - полное логирование действий пользователей и системных событий
- **Работа с языками**, концепциями и словарями (multilingual)
- **Redis** для токенов и rate limiting
- **Docker-контейнеризация** с nginx для production
- **Health check endpoint** для мониторинга
- **CORS** настройки для работы с фронтендом
- **Миграции базы данных** через Alembic
- **CI/CD** с GitHub Actions

## Быстрый старт

### Предварительные требования

- Docker и Docker Compose установлены
- Python 3.11+ (для локальной разработки)

### Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone <your-repo-url>
cd backend
```

2. Создайте файл `.env` из примера:
```bash
cp .env.example .env
```

3. Отредактируйте `.env` файл и установите свои значения (особенно `JWT_SECRET_KEY`)

4. Запустите приложение с помощью Docker Compose:

**Для разработки (рекомендуется):**
```bash
docker-compose -f docker-compose.dev.yml up
```

**Для production:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

5. Приложение будет доступно:
   - **GraphQL Playground**: http://localhost:8000/graphql
   - **Health Check**: http://localhost:8000/health
   - **MailPit Web UI** (dev only): http://localhost:8025

6. **Автоматическая инициализация данных:**
   При первом запуске база данных автоматически заполнится тестовыми данными:
   - 8 языков (ru, en, es, fr, de, zh, ja, ar)
   - 5 ролей с детализированными правами доступа
   - 5 тестовых пользователей (см. [scripts/README.md](scripts/README.md))
   - ~80 концепций в иерархической структуре
   - ~150 словарных переводов

   **Тестовые учетные записи:**
   - `admin / Admin123!` - полный доступ
   - `moderator / Moderator123!` - управление пользователями
   - `editor / Editor123!` - управление контентом
   - `testuser / User123!` - обычный пользователь

### Локальная разработка без Docker

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Убедитесь, что PostgreSQL запущен и доступен

3. Создайте файл `.env` с настройками базы данных

4. Запустите приложение:
```bash
python app.py
```

## GraphQL API

### Генерация схемы

Для экспорта GraphQL схемы в файл используйте команду:
```bash
strawberry export-schema schemas.schema:schema > schema.graphql
```

### Примеры запросов

GraphQL Playground доступен по адресу `/graphql` и содержит интерактивную документацию по API.

**Быстрый старт:**
- 📖 [Quick Start Guide](docs/QUICK_START.md) - Быстрое начало работы с API
- 📚 [GraphQL Examples](docs/graphql-examples.md) - Подробные примеры всех запросов

**Примеры для копирования:**

<details>
<summary>🔐 Авторизация (клик для раскрытия)</summary>

```graphql
mutation Login {
  login(input: {
    username: "admin"
    password: "Admin123!"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

После получения `accessToken`, добавьте в HTTP HEADERS:
```json
{
  "Authorization": "Bearer ВАШ_ACCESS_TOKEN"
}
```
</details>

<details>
<summary>👤 Получить информацию о пользователе</summary>

```graphql
query GetCurrentUser {
  me {
    id
    username
    email
    profile {
      firstName
      lastName
    }
  }
}
```
</details>

<details>
<summary>🌍 Получить список языков</summary>

```graphql
query GetLanguages {
  languages {
    id
    code
    name
  }
}
```
</details>

<details>
<summary>🗂️ Получить концепции с переводами</summary>

```graphql
query GetConceptsWithTranslations {
  concepts {
    id
    path
    depth
    dictionaries {
      name
      language {
        code
        name
      }
    }
  }
}
```
</details>

<details>
<summary>📁 Загрузить аватар</summary>

```graphql
mutation UploadAvatar($file: Upload!) {
  uploadAvatar(file: $file) {
    id
    filename
    url
    thumbnailUrl
    mimeType
    sizeMb
    width
    height
  }
}
```

**Примечание:** Загрузка файлов требует multipart/form-data. Используйте GraphQL Playground или см. [TESTING_GUIDE.md](TESTING_GUIDE.md) для примеров.
</details>

<details>
<summary>📋 Просмотр audit логов</summary>

```graphql
query MyAuditLogs {
  myAuditLogs(limit: 10) {
    logs {
      id
      action
      entityType
      description
      status
      createdAt
    }
    total
    hasMore
  }
}
```
</details>

## Структура проекта

```
backend/
├── .github/
│   └── workflows/       # GitHub Actions CI/CD
├── alembic/             # Миграции базы данных
│   └── versions/        # Файлы миграций
├── auth/                # Модуль аутентификации
│   ├── dependencies/    # Зависимости для авторизации
│   ├── models/          # Модели User, Role, Permission, Profile, OAuth
│   ├── schemas/         # GraphQL схемы для auth
│   ├── services/        # AuthService, UserService, OAuthService, TokenService
│   └── utils/           # JWT, security утилиты
├── core/                # Ядро приложения
│   ├── models/          # Базовые модели
│   │   ├── base.py      # BaseModel
│   │   ├── file.py      # Модель File (загруженные файлы)
│   │   └── audit_log.py # Модель AuditLog (логирование действий)
│   ├── services/        # Бизнес-логика
│   │   ├── file_service.py  # Работа с файлами
│   │   └── audit_service.py # Аудит логирование
│   ├── schemas/         # GraphQL схемы
│   │   ├── schema.py    # Главная схема (объединение всех модулей)
│   │   ├── file.py      # API для файлов
│   │   └── audit.py     # API для аудит логов
│   ├── database.py      # Подключение к БД
│   ├── init_db.py       # Инициализация БД и создание таблиц
│   ├── email_service.py # Email сервис (верификация, сброс пароля)
│   ├── redis_client.py  # Redis клиент
│   └── file_storage.py  # Работа с файловой системой
├── languages/           # Модуль работы с языками
│   ├── models/          # Модели Language, Concept, Dictionary
│   ├── schemas/         # GraphQL схемы для languages
│   └── services/        # Бизнес-логика languages
├── templates/           # Jinja2 шаблоны
│   └── emails/          # Email шаблоны (верификация, сброс пароля)
├── nginx/               # Nginx конфигурация (production)
│   ├── nginx.conf       # Production config
│   └── nginx.dev.conf   # Development config
├── docs/                # Документация
│   ├── QUICK_START.md         # Быстрое начало работы
│   ├── graphql-examples.md    # Примеры GraphQL запросов
│   ├── OAUTH_SETUP.md         # Настройка OAuth
│   ├── EMAIL_VERIFICATION_FLOW.md  # Email верификация
│   └── AUTH_IMPROVEMENTS.md   # Улучшения аутентификации
├── scripts/             # Скрипты
│   ├── seed_data.py     # Инициализация данных
│   └── README.md        # Описание тестовых данных
├── tests/               # Тесты
│   ├── conftest.py            # Фикстуры pytest
│   ├── test_app.py            # Тесты приложения
│   ├── test_oauth.py          # Тесты OAuth
│   ├── test_email_service.py  # Тесты email
│   └── test_email_verification.py  # Тесты верификации
├── app.py               # Точка входа приложения
├── requirements.txt     # Python зависимости
├── pytest.ini           # Конфигурация pytest
├── alembic.ini          # Конфигурация Alembic
├── .pre-commit-config.yaml  # Pre-commit хуки
├── Dockerfile           # Docker конфигурация
├── docker-compose.yml   # Basic Docker Compose
├── docker-compose.dev.yml   # Development (MailPit, hot-reload)
├── docker-compose.prod.yml  # Production (Nginx, SSL)
├── .env.example         # Пример переменных окружения
├── .env.production      # Пример production env
├── .gitignore           # Git ignore правила
├── LICENSE              # MIT License
├── uploads/             # Загруженные файлы
│   └── thumbnails/      # Автоматические превью изображений
├── README.md            # Главная документация
├── CLAUDE.md            # Гайд для Claude Code
├── CONTRIBUTING.md      # Гайд для контрибьюторов
├── ARCHITECTURE.md      # Архитектура проекта
├── DEPLOYMENT.md        # Гайд по деплою
├── TESTING_GUIDE.md     # Руководство по тестированию
└── BACKLOG.md           # Бэклог пользовательских историй
```

## База данных

### Миграции

Для создания новой миграции:
```bash
alembic revision --autogenerate -m "Описание изменений"
```

Для применения миграций:
```bash
alembic upgrade head
```

### Модели данных

Проект использует следующие основные модели:

**Auth модуль:**
- **User** - Пользователи системы
- **Role** - Роли пользователей (admin, moderator, editor, user)
- **Permission** - Права доступа (user.create, concept.edit, etc.)
- **Profile** - Профили пользователей (firstName, lastName, bio, avatar)
- **OAuthConnection** - OAuth связи (Google, Telegram)

**Core модуль:**
- **File** - Загруженные файлы (аватары, изображения, attachments) с метаданными
- **AuditLog** - Логи действий пользователей (login, CRUD операции, изменения)

**Languages модуль:**
- **Language** - Языки (ru, en, es, fr, etc.)
- **Concept** - Иерархические концепции (древовидная структура)
- **Dictionary** - Переводы концепций на разные языки

## Конфигурация

Основные переменные окружения (см. `.env.example`):

**Безопасность:**
- `JWT_SECRET_KEY` - Секретный ключ для JWT (обязательно измените!)
- `JWT_ALGORITHM` - Алгоритм JWT (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Срок жизни access token (30 минут)
- `REFRESH_TOKEN_EXPIRE_DAYS` - Срок жизни refresh token (7 дней)

**База данных:**
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - Настройки PostgreSQL
- `DATABASE_URL` - Полный URL подключения

**Redis:**
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD` - Настройки Redis

**Email:**
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` - SMTP сервер
- `SMTP_USE_TLS` - Использовать TLS (True для production)
- `FROM_EMAIL` - Email отправителя
- `FRONTEND_URL` - URL фронтенда для ссылок в письмах

**OAuth:**
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` - Google OAuth
- `TELEGRAM_BOT_TOKEN` - Telegram OAuth

**Приложение:**
- `APP_HOST`, `APP_PORT` - Настройки приложения
- `DEBUG` - Режим отладки (False для production)
- `SEED_DATABASE` - Автоматическое заполнение тестовыми данными (false для production)
- `ALLOWED_ORIGINS` - Разрешенные CORS origins (через запятую)
- `UPLOAD_DIR` - Директория для загружаемых файлов (по умолчанию `uploads`)

## OAuth и Email

### OAuth Аутентификация

Приложение поддерживает вход через:
- **Google OAuth 2.0** - Sign in with Google
- **Telegram Login Widget** - Sign in with Telegram

**Настройка OAuth:** См. [docs/OAUTH_SETUP.md](docs/OAUTH_SETUP.md)

**Пример GraphQL запроса:**
```graphql
mutation {
  loginWithGoogle(input: { idToken: "your_google_id_token" }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

### Email Верификация

При регистрации пользователи получают email с ссылкой для верификации.

**Возможности:**
- Email верификация при регистрации
- Сброс пароля через email
- Rate limiting (3 письма в час на email)
- Токены с TTL (24 часа для верификации, 1 час для сброса)

**Настройка:** См. [docs/EMAIL_VERIFICATION_FLOW.md](docs/EMAIL_VERIFICATION_FLOW.md)

**Тестирование в development:**
- MailPit Web UI: http://localhost:8025
- Все письма перехватываются и отображаются в MailPit

## Разработка

### Стиль кода

Проект следует PEP 8 стандартам Python с 100-символьным лимитом строки.

### Тестирование

```bash
# Запустить все тесты
pytest

# Запустить с покрытием
pytest --cov=. --cov-report=html

# Запустить только unit тесты
pytest -m unit

# Запустить только integration тесты
pytest -m integration
```

## Production развертывание

**Полный гайд:** См. [DEPLOYMENT.md](DEPLOYMENT.md)

### Два варианта деплоя:

**1. VPS/Dedicated Server с Nginx (рекомендуется):**
```bash
docker-compose -f docker-compose.prod.yml up -d
```
Включает nginx для SSL, rate limiting, сжатия.

**2. Cloud Platform (AWS/GCP/Azure):**
Без nginx - облачный балансировщик нагрузки обрабатывает всё.

### Чеклист перед деплоем:

- [ ] Изменить `JWT_SECRET_KEY` на случайное значение
- [ ] Установить сильные пароли БД и Redis
- [ ] Установить `SEED_DATABASE=false`
- [ ] Установить `DEBUG=False`
- [ ] Настроить production SMTP (SendGrid/AWS SES)
- [ ] Обновить `ALLOWED_ORIGINS` на production домен
- [ ] Настроить SSL сертификат (Let's Encrypt)
- [ ] Настроить OAuth credentials для production
- [ ] Запустить миграции базы данных
- [ ] Настроить бэкапы (БД + Redis)

## 📚 Документация

### Основные документы

| Документ | Описание | Для кого |
|----------|----------|----------|
| **[DOCS_STRUCTURE.md](DOCS_STRUCTURE.md)** | 🗺️ Навигация по всей документации | Все |
| **[CHANGELOG.md](CHANGELOG.md)** | 📝 История изменений проекта | Разработчики, DevOps |
| **[BACKLOG.md](BACKLOG.md)** | 📋 Планы развития и задачи | Product, разработчики |
| **[CLAUDE.md](CLAUDE.md)** | 🤖 Полное руководство для Claude Code | Разработчики |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | 🏗️ Архитектура проекта | Разработчики, архитекторы |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | 🚀 Развертывание в production | DevOps, администраторы |
| **[TESTING_GUIDE.md](TESTING_GUIDE.md)** | 🧪 Тестирование функций | QA, разработчики |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | 🤝 Как внести вклад | Контрибьюторы |

### Детальная документация (docs/)

- **[docs/QUICK_START.md](docs/QUICK_START.md)** - Быстрый старт с примерами
- **[docs/graphql-examples.md](docs/graphql-examples.md)** - Примеры GraphQL запросов
- **[docs/OAUTH_SETUP.md](docs/OAUTH_SETUP.md)** - Настройка Google и Telegram OAuth
- **[docs/EMAIL_VERIFICATION_FLOW.md](docs/EMAIL_VERIFICATION_FLOW.md)** - Email верификация и сброс пароля
- **[docs/AUTH_IMPROVEMENTS.md](docs/AUTH_IMPROVEMENTS.md)** - Улучшения аутентификации

### 🎯 Быстрые ссылки

**Новичкам:** [README.md](README.md) → [ARCHITECTURE.md](ARCHITECTURE.md) → [docs/QUICK_START.md](docs/QUICK_START.md)

**Разработчикам:** [CLAUDE.md](CLAUDE.md) → [TESTING_GUIDE.md](TESTING_GUIDE.md) → [CONTRIBUTING.md](CONTRIBUTING.md)

**DevOps:** [DEPLOYMENT.md](DEPLOYMENT.md) → [CHANGELOG.md](CHANGELOG.md)

**Контрибьюторам:** [BACKLOG.md](BACKLOG.md) → [CONTRIBUTING.md](CONTRIBUTING.md) → [ARCHITECTURE.md](ARCHITECTURE.md)

## Лицензия

MIT License - см. [LICENSE](LICENSE)

## Ключевые возможности

- Модульная архитектура (легко расширять)
- Строгое разделение на models/services/schemas
- Автоматическое заполнение тестовыми данными
- Полное покрытие тестами
- CI/CD с GitHub Actions
- Docker для простого деплоя
- Production-ready с nginx
- OAuth и email верификация из коробки