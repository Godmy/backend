# Dictionary (Translation) Mutations

**Required:** Authorization header

## Create Translation

Create a new translation for a concept.

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

**Validation:**
- Concept must exist
- Language must exist
- One translation per concept-language pair (unique constraint)

---

## Update Translation

Update existing translation.

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

---

## Delete Translation

Soft delete a translation.

```graphql
mutation DeleteDictionary {
  deleteDictionary(id: 100)  # Returns boolean
}
```

**Notes:**
- Uses soft delete (can be restored by admin)
- Does not delete the concept itself

---

## Bulk Add Translations

Add translations for a concept in multiple languages:

```graphql
mutation AddTranslations {
  ru: createDictionary(input: {
    conceptId: 100
    languageId: 1
    name: "Технологии"
    description: "Различные технологии и инструменты"
  }) {
    id
    name
  }

  en: createDictionary(input: {
    conceptId: 100
    languageId: 2
    name: "Technology"
    description: "Various technologies and tools"
  }) {
    id
    name
  }

  es: createDictionary(input: {
    conceptId: 100
    languageId: 3
    name: "Tecnología"
    description: "Varias tecnologías y herramientas"
  }) {
    id
    name
  }
}
```

---

## Implementation

- `languages/models/dictionary.py` - DictionaryModel
- `languages/schemas/dictionary.py` - GraphQL schema
- `languages/services/dictionary_service.py` - Business logic

**Relationships:**
- `Language` ← `Dictionary` → `Concept`
- Translations link language to concepts
