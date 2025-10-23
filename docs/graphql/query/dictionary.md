# Dictionary (Translation) Queries

Dictionaries provide translations for concepts in different languages.

## Get Translation by Concept and Language

Get specific translation for a concept in a specific language.

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

---

## Get All Translations for Concept

Get all translations for a specific concept.

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

---

## Get Translations by Language

Get all translations in a specific language.

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

---

## Get Concept Hierarchy with Translations

Get complete hierarchy with translations in all languages.

```graphql
query GetHierarchyWithTranslations {
  concepts {
    id
    path
    depth
    parentId
    dictionaries {
      name
      description
      language {
        code
      }
    }
  }
}
```

---

## Dictionary Fields

- `id` - Unique identifier
- `name` - Short name/title of the concept in this language
- `description` - Longer description (optional)
- `image` - Image URL (optional)
- `conceptId` - Foreign key to concept
- `languageId` - Foreign key to language

---

## Implementation

- `languages/models/dictionary.py` - DictionaryModel
- `languages/schemas/dictionary.py` - GraphQL schema
- `languages/services/dictionary_service.py` - Business logic
