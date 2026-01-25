# Quick Start - GraphQL API

Быстрое руководство для начала работы с API МультиПУЛЬТ.

## 🚀 Запуск проекта

```bash
docker-compose up -d
```

Откройте: http://localhost:8000/graphql

## 🔐 Авторизация (копируйте и вставляйте)

### 1. Войти как Администратор

```graphql
mutation {
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

### 2. Скопируйте accessToken и добавьте в HTTP HEADERS:

```json
{
  "Authorization": "Bearer ВАШ_ACCESS_TOKEN"
}
```

**Где находятся HTTP HEADERS?** Внизу страницы Playground есть секция "HTTP HEADERS".

## 👤 Тестовые аккаунты

| Логин     | Пароль        | Роль          |
|-----------|---------------|---------------|
| admin     | Admin123!     | Администратор |
| moderator | Moderator123! | Модератор     |
| editor    | Editor123!    | Редактор      |
| testuser  | User123!      | Пользователь  |

## 📋 Базовые запросы

### Получить информацию о себе (после авторизации)

```graphql
query {
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

### Получить все языки

```graphql
query {
  languages {
    id
    code
    name
  }
}
```

### Получить все концепции

```graphql
query {
  concepts {
    id
    path
    depth
    dictionaries {
      name
      language {
        code
      }
    }
  }
}
```

## ✏️ Базовые мутации

### Создать язык

```graphql
mutation {
  createLanguage(input: {
    code: "pt"
    name: "Português"
  }) {
    id
    code
    name
  }
}
```

### Создать концепцию

```graphql
mutation {
  createConcept(input: {
    path: "sports"
    depth: 0
  }) {
    id
    path
    depth
  }
}
```

### Добавить перевод

```graphql
mutation {
  createDictionary(input: {
    conceptId: 1
    languageId: 1
    name: "Цвета"
    description: "Основные цвета"
  }) {
    id
    name
  }
}
```

## 🎯 Полный пример: Создание новой категории с переводами

### Шаг 1: Авторизация

```graphql
mutation {
  login(input: {username: "admin", password: "Admin123!"}) {
    accessToken
  }
}
```

### Шаг 2: Создать концепцию

```graphql
mutation {
  createConcept(input: {path: "vehicles", depth: 0}) {
    id
  }
}
```

**Запомните возвращенный `id` (например, 100)**

### Шаг 3: Добавить русский перевод

```graphql
mutation {
  createDictionary(input: {
    conceptId: 100
    languageId: 1
    name: "Транспорт"
    description: "Средства передвижения"
  }) {
    id
  }
}
```

### Шаг 4: Добавить английский перевод

```graphql
mutation {
  createDictionary(input: {
    conceptId: 100
    languageId: 2
    name: "Vehicles"
    description: "Means of transportation"
  }) {
    id
  }
}
```

### Шаг 5: Проверить результат

```graphql
query {
  concept(id: 100) {
    path
    dictionaries {
      name
      description
      language {
        code
        name
      }
    }
  }
}
```

## 🛠️ Полезные команды

### Проверить статус приложения

```bash
curl http://localhost:8000/health
```

### Просмотреть логи

```bash
docker-compose logs -f app
```

### Перезапустить

```bash
docker-compose restart app
```

### Остановить

```bash
docker-compose down
```

### Пересоздать с новыми данными

```bash
docker-compose down -v
docker-compose up -d
```

## 📚 Подробная документация

- **Полные примеры запросов**: [graphql-examples.md](./graphql-examples.md)
- **Архитектура проекта**: [../ARCHITECTURE.md](../ARCHITECTURE.md)
- **Тестовые данные**: [../scripts/README.md](../scripts/README.md)

## ⚡ Горячие клавиши Playground

- `Ctrl+Space` - Автодополнение
- `Ctrl+Enter` - Выполнить запрос
- `Ctrl+Shift+P` - Форматировать запрос
- Кнопка "Docs" справа - Документация схемы

## 🆘 Решение проблем

**Проблема**: "Not authenticated"
- **Решение**: Добавьте `Authorization` заголовок с токеном

**Проблема**: "Connection refused"
- **Решение**: Проверьте, что контейнеры запущены: `docker-compose ps`

**Проблема**: "Invalid credentials"
- **Решение**: Проверьте правильность username и password

**Проблема**: "Already exists"
- **Решение**: Данные уже созданы, используйте update вместо create

## 🎓 Дальнейшие шаги

1. Изучите [graphql-examples.md](./graphql-examples.md) для более сложных запросов
2. Попробуйте создать свою иерархию концепций
3. Добавьте переводы на разные языки
4. Экспериментируйте с ролями и правами доступа
