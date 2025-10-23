# Language Queries

## Get All Languages

Get list of all available languages.

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

**Expected response:**
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

---

## Get Language by ID

Get specific language by ID.

```graphql
query GetLanguageById {
  language(id: 1) {
    id
    code
    name
    createdAt
    updatedAt
  }
}
```

---

## Seeded Languages

Default languages (when `SEED_DATABASE=true`):
- Russian (ru)
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Chinese (zh)
- Japanese (ja)
- Arabic (ar)

---

## Implementation

- `languages/models/language.py` - LanguageModel
- `languages/schemas/language.py` - GraphQL schema
- `languages/services/language_service.py` - Business logic
