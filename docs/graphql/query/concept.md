# Concept Queries

## Get All Concepts

Get list of all concepts.

```graphql
query GetConcepts {
  concepts {
    id
    path
    depth
    parentId
    createdAt
    updatedAt
  }
}
```

---

## Get Concept by ID

Get specific concept by ID with translations.

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

---

## Get Child Concepts

Get child concepts by parent ID.

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

**Notes:**
- Returns direct children only (not recursive)
- Filter by parent ID to build hierarchy

---

## Get Root Concepts

Get top-level concepts (depth = 0).

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

Then filter results where `depth === 0` in your client code.

---

## Concept Hierarchy

Concepts use **materialized path pattern**:
- Hierarchical structure with `parent_id` relationship
- Path stored as string (e.g., `/root/parent/child/`)
- Depth indicates nesting level (0 = root)

**Example hierarchy:**
```
colors (depth: 0, path: "colors")
  └── red (depth: 1, path: "colors.red", parentId: 1)
      └── dark_red (depth: 2, path: "colors.red.dark_red", parentId: 10)
```

---

## Implementation

- `languages/models/concept.py` - ConceptModel
- `languages/schemas/concept.py` - GraphQL schema
- `languages/services/concept_service.py` - Business logic
