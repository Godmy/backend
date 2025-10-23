# GraphQL Queries Documentation

This directory contains documentation for all GraphQL queries organized by functional modules.

## Available Queries

### Authentication & User
- **[auth.md](auth.md)** - Authentication queries (me, current user)

### Admin Panel
- **[admin.md](admin.md)** - Admin queries (user management, system statistics)

### Languages
- **[language.md](language.md)** - Language queries (list languages, get by ID)

### Concepts
- **[concept.md](concept.md)** - Concept queries (hierarchy, children, by ID)

### Dictionaries (Translations)
- **[dictionary.md](dictionary.md)** - Translation queries (by concept, by language)

### Files
- **[file.md](file.md)** - File queries (my files, file metadata)

### Search
- **[search.md](search.md)** - Search queries (full-text search, suggestions, popular concepts)

### Audit Logging
- **[audit.md](audit.md)** - Audit log queries (my logs, all logs, user activity)

### Soft Delete
- **[soft_delete.md](soft_delete.md)** - Soft delete queries (deleted records)

### Import/Export
- **[import_export.md](import_export.md)** - Import/export queries (job status, my jobs)

---

## Using in GraphQL Playground

1. Open GraphQL Playground: http://localhost:8000/graphql
2. Add authorization header for protected queries:
   ```json
   {
     "Authorization": "Bearer YOUR_ACCESS_TOKEN"
   }
   ```
3. Use autocomplete (Ctrl+Space) for field suggestions
4. View schema documentation in the "Docs" panel

---

## Example Query

```graphql
query GetCurrentUserWithProfile {
  me {
    id
    username
    email
    profile {
      firstName
      lastName
      language
    }
  }
}
```

---

## See Also

- **[Mutations](../mutation/README.md)** - GraphQL mutations documentation
- **[CLAUDE.md](../../../CLAUDE.md)** - Full project documentation
