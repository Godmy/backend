# Language Mutations

**Required:** Authorization header

## Create Language

Create a new language.

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

**Validation:**
- Code must be unique
- Code typically 2-3 characters (ISO 639-1 or ISO 639-3)

---

## Update Language

Update existing language.

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

---

## Delete Language

Soft delete a language.

```graphql
mutation DeleteLanguage {
  deleteLanguage(id: 10)  # Returns boolean
}
```

**Notes:**
- Uses soft delete (can be restored by admin)
- Cannot delete language if it has translations

---

## Implementation

- `languages/models/language.py` - LanguageModel
- `languages/schemas/language.py` - GraphQL schema
- `languages/services/language_service.py` - Business logic
