# GraphQL Queries Examples

Примеры GraphQL запросов для тестирования API в GraphQL Playground.

## Аутентификация

### 1. Регистрация нового пользователя

```graphql
mutation RegisterUser {
  register(input: {
    username: "newuser"
    email: "newuser@example.com"
    password: "SecurePass123!"
    firstName: "Иван"
    lastName: "Иванов"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

**Ожидаемый результат:**
```json
{
  "data": {
    "register": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "tokenType": "bearer"
    }
  }
}
```

### 2. Вход в систему (Login)

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

**Тестовые учетные записи:**
- `admin / Admin123!` - администратор
- `moderator / Moderator123!` - модератор
- `editor / Editor123!` - редактор
- `testuser / User123!` - обычный пользователь

**Ожидаемый результат:**
```json
{
  "data": {
    "login": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "tokenType": "bearer"
    }
  }
}
```

**Важно:** Сохраните `accessToken` для использования в защищенных запросах!

### 3. Обновление токена (Refresh Token)

```graphql
mutation RefreshToken {
  refreshToken(input: {
    refreshToken: "ВАШ_REFRESH_TOKEN_ЗДЕСЬ"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

## Работа с пользователем (требуется авторизация)

### Настройка заголовков в Playground

Перед выполнением защищенных запросов добавьте заголовок авторизации:

```json
{
  "Authorization": "Bearer ВАШ_ACCESS_TOKEN_ЗДЕСЬ"
}
```

В Strawberry GraphQL Playground это делается в разделе "HTTP HEADERS" внизу страницы.

### 4. Получить информацию о текущем пользователе

```graphql
query GetCurrentUser {
  me {
    id
    username
    email
    isActive
    isVerified
    profile {
      id
      firstName
      lastName
      avatar
      language
      timezone
    }
  }
}
```

**Ожидаемый результат:**
```json
{
  "data": {
    "me": {
      "id": 1,
      "username": "admin",
      "email": "admin@multipult.dev",
      "isActive": true,
      "isVerified": true,
      "profile": {
        "id": 1,
        "firstName": "Администратор",
        "lastName": "Системы",
        "avatar": null,
        "language": "ru",
        "timezone": "UTC"
      }
    }
  }
}
```

### 5. Обновить профиль пользователя

```graphql
mutation UpdateProfile {
  updateProfile(
    firstName: "Новое Имя"
    lastName: "Новая Фамилия"
    language: "en"
    timezone: "Europe/Moscow"
  ) {
    id
    username
    email
    profile {
      firstName
      lastName
      language
      timezone
    }
  }
}
```

## Работа с языками

### 6. Получить список всех языков

```graphql
query GetLanguages {
  languages {
    id
    code
    name
    createdAt
    updatedAt
  }
}
```

**Ожидаемый результат:**
```json
{
  "data": {
    "languages": [
      {
        "id": 1,
        "code": "ru",
        "name": "Русский",
        "createdAt": "2025-10-11T10:00:00",
        "updatedAt": "2025-10-11T10:00:00"
      },
      {
        "id": 2,
        "code": "en",
        "name": "English",
        "createdAt": "2025-10-11T10:00:00",
        "updatedAt": "2025-10-11T10:00:00"
      }
    ]
  }
}
```

### 7. Получить язык по ID

```graphql
query GetLanguageById {
  language(id: 1) {
    id
    code
    name
  }
}
```

### 8. Создать новый язык (требуется авторизация)

```graphql
mutation CreateLanguage {
  createLanguage(input: {
    code: "it"
    name: "Italiano"
  }) {
    id
    code
    name
    createdAt
  }
}
```

### 9. Обновить язык (требуется авторизация)

```graphql
mutation UpdateLanguage {
  updateLanguage(
    id: 1
    input: {
      code: "ru"
      name: "Русский язык"
    }
  ) {
    id
    code
    name
    updatedAt
  }
}
```

### 10. Удалить язык (требуется авторизация)

```graphql
mutation DeleteLanguage {
  deleteLanguage(id: 10)
}
```

## Работа с концепциями

### 11. Получить все концепции

```graphql
query GetConcepts {
  concepts {
    id
    path
    depth
    parentId
    createdAt
  }
}
```

### 12. Получить концепцию по ID с переводами

```graphql
query GetConceptWithTranslations {
  concept(id: 1) {
    id
    path
    depth
    parentId
    dictionaries {
      id
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

### 13. Получить дочерние концепции

```graphql
query GetChildConcepts {
  conceptsByParent(parentId: 1) {
    id
    path
    depth
    parentId
  }
}
```

### 14. Создать концепцию (требуется авторизация)

```graphql
mutation CreateConcept {
  createConcept(input: {
    path: "sports"
    depth: 0
    parentId: null
  }) {
    id
    path
    depth
    createdAt
  }
}
```

### 15. Создать дочернюю концепцию

```graphql
mutation CreateChildConcept {
  createConcept(input: {
    path: "sports.football"
    depth: 1
    parentId: 50
  }) {
    id
    path
    depth
    parentId
  }
}
```

## Работа со словарями (переводы)

### 16. Получить перевод концепции на определенный язык

```graphql
query GetTranslation {
  dictionaryByConceptAndLanguage(
    conceptId: 10
    languageId: 1
  ) {
    id
    name
    description
    image
    concept {
      path
    }
    language {
      code
      name
    }
  }
}
```

### 17. Получить все переводы концепции

```graphql
query GetAllTranslations {
  concept(id: 10) {
    id
    path
    dictionaries {
      id
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

### 18. Создать перевод (требуется авторизация)

```graphql
mutation CreateDictionary {
  createDictionary(input: {
    conceptId: 10
    languageId: 1
    name: "Красный"
    description: "Цвет крови и огня"
    image: null
  }) {
    id
    name
    description
    concept {
      path
    }
    language {
      code
    }
  }
}
```

### 19. Обновить перевод (требуется авторизация)

```graphql
mutation UpdateDictionary {
  updateDictionary(
    id: 1
    input: {
      name: "Красный цвет"
      description: "Обновленное описание красного цвета"
    }
  ) {
    id
    name
    description
    updatedAt
  }
}
```

### 20. Удалить перевод (требуется авторизация)

```graphql
mutation DeleteDictionary {
  deleteDictionary(id: 100)
}
```

## Комплексные запросы

### 21. Получить иерархию концепций с переводами

```graphql
query GetHierarchyWithTranslations {
  concepts {
    id
    path
    depth
    parentId
    dictionaries {
      name
      language {
        code
      }
    }
  }
}
```

### 22. Поиск переводов по языку

```graphql
query SearchByLanguage {
  dictionariesByLanguage(languageId: 1) {
    id
    name
    description
    concept {
      path
      depth
    }
  }
}
```

### 23. Получить все концепции верхнего уровня (depth = 0)

```graphql
query GetRootConcepts {
  concepts {
    id
    path
    depth
    parentId
  }
}
```

Затем отфильтруйте в коде результаты где `depth === 0`.

## Полный пример workflow

### Шаг 1: Авторизация

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

### Шаг 2: Установить заголовок

В HTTP HEADERS:
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Шаг 3: Получить информацию о себе

```graphql
query Me {
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

### Шаг 4: Создать новую концепцию

```graphql
mutation CreateNewConcept {
  createConcept(input: {
    path: "technology"
    depth: 0
    parentId: null
  }) {
    id
    path
  }
}
```

### Шаг 5: Добавить переводы для концепции

```graphql
mutation AddTranslations {
  ru: createDictionary(input: {
    conceptId: 100
    languageId: 1
    name: "Технологии"
  }) {
    id
    name
  }

  en: createDictionary(input: {
    conceptId: 100
    languageId: 2
    name: "Technology"
  }) {
    id
    name
  }
}
```

## Обработка ошибок

### Пример ошибки - неверный пароль

```graphql
mutation LoginFailed {
  login(input: {
    username: "admin"
    password: "wrongpassword"
  }) {
    accessToken
  }
}
```

**Ответ:**
```json
{
  "data": null,
  "errors": [
    {
      "message": "Invalid credentials",
      "locations": [...],
      "path": ["login"]
    }
  ]
}
```

### Пример ошибки - отсутствует авторизация

```graphql
query WithoutAuth {
  me {
    username
  }
}
```

**Ответ:**
```json
{
  "data": null,
  "errors": [
    {
      "message": "Not authenticated",
      "locations": [...],
      "path": ["me"]
    }
  ]
}
```

## Советы по работе с Playground

1. **Автодополнение**: Нажмите `Ctrl+Space` для автодополнения
2. **Документация**: Нажмите на кнопку "Docs" справа для просмотра схемы
3. **Форматирование**: Нажмите `Ctrl+Shift+P` (или `Cmd+Shift+P` на Mac) для форматирования запроса
4. **История**: Ваши запросы сохраняются в истории браузера
5. **Множественные запросы**: Можете выполнять несколько операций в одном запросе, используя алиасы

## Дополнительные ресурсы

- GraphQL Playground: http://localhost:8000/graphql
- Health Check: http://localhost:8000/health
- Документация API: Кнопка "Docs" в Playground
