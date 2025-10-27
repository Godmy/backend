# 📚 Структура документации

Навигация по всей документации проекта МультиПУЛЬТ.

## 🗂️ Организация документов

```
backend/
├── 📖 Основная документация (корень)
│   ├── README.md              # Главная страница проекта
│   ├── CHANGELOG.md           # История изменений
│   ├── BACKLOG.md             # Бэклог и планы развития
│   ├── CLAUDE.md              # Гайд для разработки с Claude Code
│   ├── ARCHITECTURE.md        # Архитектура проекта
│   ├── DEPLOYMENT.md          # Руководство по развертыванию
│   ├── CONTRIBUTING.md        # Как внести вклад
│   ├── TESTING_GUIDE.md       # Руководство по тестированию
│   └── LICENSE                # MIT лицензия
│
└── 📁 docs/                   # Детальная документация
    ├── QUICK_START.md         # Быстрый старт
    ├── graphql-examples.md    # Примеры GraphQL запросов
    ├── OAUTH_SETUP.md         # Настройка OAuth провайдеров
    ├── EMAIL_VERIFICATION_FLOW.md  # Email верификация
    └── AUTH_IMPROVEMENTS.md   # Улучшения аутентификации
```

---

## 📄 Описание документов

### 🏠 Главная документация

#### [README.md](README.md)
**Первая точка входа в проект**
- Обзор проекта и технологий
- Быстрый старт (установка, запуск)
- Примеры GraphQL запросов
- Структура проекта
- Конфигурация и переменные окружения
- Ссылки на всю остальную документацию

**Читать первым:** ✅ Да
**Аудитория:** Все (разработчики, контрибьюторы, пользователи)

---

#### [CHANGELOG.md](CHANGELOG.md)
**История всех изменений проекта**
- Что нового в каждой версии
- Добавленные функции
- Исправленные баги
- Breaking changes
- Следует формату [Keep a Changelog](https://keepachangelog.com/)

**Читать первым:** ❌ Нет
**Когда читать:** При обновлении версии, чтобы узнать что изменилось
**Аудитория:** Разработчики, DevOps, пользователи API

**Актуальная версия:** v0.3.0 (File Upload & Audit Logging)

---

#### [BACKLOG.md](BACKLOG.md)
**Планы развития и пользовательские истории**
- Top 10 приоритетных задач
- Пользовательские истории с acceptance criteria
- Story points и оценки сложности
- Статусы задач (Backlog, In Progress, Done)
- Приоритеты (P0-P3)

**Читать первым:** ❌ Нет
**Когда читать:** При планировании новых функций
**Аудитория:** Product managers, разработчики, контрибьюторы

**Выполнено:** File Upload System ✅, Audit Logging ✅
**В планах:** Advanced Search, User Profile Management, Rate Limiting

---

#### [CLAUDE.md](CLAUDE.md)
**Полное руководство для разработки с Claude Code**
- Development команды (Docker, pytest, миграции)
- Архитектура и модульная структура
- Паттерны и соглашения
- Email система (MailPit, верификация)
- **File Upload System** (новое!)
- **Audit Logging System** (новое!)
- OAuth аутентификация
- Deployment чеклисты
- Code style и тестирование

**Читать первым:** ✅ Да, если используете Claude Code
**Аудитория:** Разработчики с Claude Code

**Объем:** ~800 строк, очень подробный

---

#### [ARCHITECTURE.md](ARCHITECTURE.md)
**Архитектура и структура проекта**
- Модульная организация (core, auth, languages)
- Разделение ответственности (models/services/schemas)
- Поток данных (GraphQL → Services → Models)
- Связи между моделями
- Тестирование и CI/CD
- Расширение проекта (добавление модулей)

**Читать первым:** ✅ Да, перед началом разработки
**Аудитория:** Разработчики, архитекторы

**Ключевые концепции:**
- Модульность
- Separation of Concerns
- GraphQL-agnostic services

---

#### [DEPLOYMENT.md](DEPLOYMENT.md)
**Руководство по развертыванию в production**
- Docker Compose для VPS/Dedicated серверов
- Cloud deployment (AWS, GCP, Azure)
- Nginx конфигурация
- SSL/TLS настройка (Let's Encrypt)
- Production чеклист
- Мониторинг и логирование
- Бэкапы базы данных

**Читать первым:** ❌ Нет
**Когда читать:** Перед деплоем в production
**Аудитория:** DevOps, системные администраторы

---

#### [CONTRIBUTING.md](CONTRIBUTING.md)
**Как внести вклад в проект**
- Code style и соглашения
- Pull request процесс
- Тестирование требований
- Pre-commit хуки
- Структура коммитов

**Читать первым:** ❌ Нет
**Когда читать:** Перед созданием PR
**Аудитория:** Open-source контрибьюторы

---

#### [TESTING_GUIDE.md](TESTING_GUIDE.md)
**Руководство по тестированию новых функций**
- Тестирование File Upload System
- Тестирование Audit Logging
- GraphQL Playground примеры
- cURL команды
- Python примеры
- Troubleshooting
- Database inspection

**Читать первым:** ❌ Нет
**Когда читать:** При тестировании File Upload или Audit Logging
**Аудитория:** QA, разработчики, тестировщики

**Создан:** 2025-01-16 (новый!)

---

### 📁 Детальная документация (docs/)

#### [docs/QUICK_START.md](docs/QUICK_START.md)
**Быстрый старт с пошаговыми инструкциями**
- От установки до первого запроса
- Примеры для копирования
- Частые ошибки и решения

**Читать первым:** ✅ Да, для новичков
**Аудитория:** Начинающие разработчики

---

#### [docs/graphql-examples.md](docs/graphql-examples.md)
**Коллекция GraphQL запросов**
- Примеры всех queries и mutations
- Комментарии к параметрам
- Ожидаемые ответы

**Читать первым:** ❌ Нет
**Когда читать:** При работе с API
**Аудитория:** Frontend разработчики, API пользователи

---

#### [docs/OAUTH_SETUP.md](docs/OAUTH_SETUP.md)
**Настройка OAuth провайдеров**
- Google OAuth 2.0 (пошагово)
- Telegram Login Widget (пошагово)
- Получение credentials
- Тестирование OAuth flow

**Читать первым:** ❌ Нет
**Когда читать:** При настройке OAuth
**Аудитория:** Разработчики, DevOps

---

#### [docs/EMAIL_VERIFICATION_FLOW.md](docs/EMAIL_VERIFICATION_FLOW.md)
**Email верификация и сброс пароля**
- Архитектура email системы
- Redis для токенов
- MailPit для тестирования
- Production SMTP настройка

**Читать первым:** ❌ Нет
**Когда читать:** При работе с email функционалом
**Аудитория:** Backend разработчики

---

#### [docs/GRAPHQL_PLAYGROUND_GUIDE.md](docs/GRAPHQL_PLAYGROUND_GUIDE.md)
**Руководство по GraphQL Playground**
- Настройка и конфигурация
- Функции и возможности
- Примеры использования
- Безопасность и аутентификация

**Читать первым:** ❌ Нет
**Когда читать:** При работе с GraphQL API
**Аудитория:** Frontend разработчики, API пользователи

---

## 🎯 Где найти информацию о...

### Быстрые ссылки по темам:

| Тема | Документ | Раздел |
|------|----------|--------|
| **Установка и запуск** | [README.md](README.md) | Быстрый старт |
| **Docker команды** | [CLAUDE.md](CLAUDE.md) | Running the Application |
| **GraphQL примеры** | [README.md](README.md) | GraphQL API → Примеры |
| **Загрузка файлов** | [TESTING_GUIDE.md](TESTING_GUIDE.md) | Testing File Upload |
| **Audit логи** | [TESTING_GUIDE.md](TESTING_GUIDE.md) | Testing Audit Logging |
| **OAuth настройка** | [docs/OAUTH_SETUP.md](docs/OAUTH_SETUP.md) | Вся страница |
| **Email верификация** | [docs/EMAIL_VERIFICATION_FLOW.md](docs/EMAIL_VERIFICATION_FLOW.md) | Вся страница |
| **Архитектура** | [ARCHITECTURE.md](ARCHITECTURE.md) | Вся страница |
| **Deployment** | [DEPLOYMENT.md](DEPLOYMENT.md) | Вся страница |
| **Миграции БД** | [CLAUDE.md](CLAUDE.md) | Database Operations |
| **Тестирование** | [CLAUDE.md](CLAUDE.md) | Testing Strategy |
| **Code style** | [CONTRIBUTING.md](CONTRIBUTING.md) | Code Style |
| **Что нового** | [CHANGELOG.md](CHANGELOG.md) | Последняя версия |
| **Планы развития** | [BACKLOG.md](BACKLOG.md) | Top 10 задач |

---

## 🚀 Рекомендуемый порядок чтения

### Для новых разработчиков:

1. **[README.md](README.md)** - обзор проекта
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** - понимание структуры
3. **[docs/QUICK_START.md](docs/QUICK_START.md)** - практика
4. **[CLAUDE.md](CLAUDE.md)** - полное руководство
5. **[CONTRIBUTING.md](CONTRIBUTING.md)** - перед первым PR

### Для контрибьюторов:

1. **[README.md](README.md)** - обзор
2. **[BACKLOG.md](BACKLOG.md)** - что можно сделать
3. **[CONTRIBUTING.md](CONTRIBUTING.md)** - правила
4. **[ARCHITECTURE.md](ARCHITECTURE.md)** - структура

### Для DevOps:

1. **[README.md](README.md)** - обзор
2. **[DEPLOYMENT.md](DEPLOYMENT.md)** - развертывание
3. **[CHANGELOG.md](CHANGELOG.md)** - версии
4. **[CLAUDE.md](CLAUDE.md) → Production Checklist**

### Для тестировщиков:

1. **[README.md](README.md)** - обзор
2. **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - тестирование
3. **[docs/graphql-examples.md](docs/graphql-examples.md)** - примеры API

---

## 📝 Поддержание документации

### Когда обновлять:

- **CHANGELOG.md** - при каждом релизе (версии)
- **BACKLOG.md** - при добавлении/завершении задач
- **README.md** - при добавлении новых функций
- **CLAUDE.md** - при изменении архитектуры
- **ARCHITECTURE.md** - при добавлении модулей
- **TESTING_GUIDE.md** - при добавлении тестируемых функций

### Контрольный список для PR:

- [ ] Обновлен CHANGELOG.md с изменениями
- [ ] README.md содержит новые функции
- [ ] Обновлен BACKLOG.md (если применимо)
- [ ] Добавлены примеры в docs/graphql-examples.md
- [ ] ARCHITECTURE.md отражает изменения структуры
- [ ] TESTING_GUIDE.md содержит инструкции по тестированию

---

## 🔗 Внешние ресурсы

- [Strawberry GraphQL Docs](https://strawberry.rocks/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)

---

**Последнее обновление:** 2025-01-16
**Версия проекта:** 0.3.0
