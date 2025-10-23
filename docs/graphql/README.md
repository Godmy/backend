# GraphQL API Documentation

Complete GraphQL API documentation organized by functional modules.

## Structure

This documentation is organized into two main sections:

### 📖 [Queries](query/README.md)
Read operations for fetching data:
- Authentication & User Management
- Admin Panel
- Languages, Concepts, Dictionaries
- Files & Search
- Audit Logs & Soft Delete
- Import/Export Status

### ✏️ [Mutations](mutation/README.md)
Write operations for creating, updating, and deleting data:
- Registration & Authentication
- User Profile Management
- Admin Operations
- Content Management (Languages, Concepts, Translations)
- File Uploads
- Data Import/Export

---

## Quick Start

### 1. Start the Application

```bash
# Development mode with hot-reload
docker-compose -f docker-compose.dev.yml up
```

### 2. Access GraphQL Playground

Open in browser:
```
http://localhost:8000/graphql
```

### 3. Authenticate

First, login to get access token:

```graphql
mutation Login {
  login(input: {
    username: "admin"
    password: "Admin123!"
  }) {
    accessToken
    refreshToken
  }
}
```

### 4. Set Authorization Header

In GraphQL Playground, click "HTTP HEADERS" at the bottom and add:

```json
{
  "Authorization": "Bearer YOUR_ACCESS_TOKEN_HERE"
}
```

### 5. Make Queries

Now you can make authenticated requests:

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

---

## Documentation by Module

### Authentication
- **Queries:** [auth.md](query/auth.md) - Get current user
- **Mutations:** [auth.md](mutation/auth.md) - Register, login, OAuth, password reset

### User Profile
- **Mutations:** [profile.md](mutation/profile.md) - Update profile, change password/email

### Admin Panel
- **Queries:** [admin.md](query/admin.md) - User list, system statistics
- **Mutations:** [admin.md](mutation/admin.md) - Ban users, bulk role management

### Languages
- **Queries:** [language.md](query/language.md) - List languages
- **Mutations:** [language.md](mutation/language.md) - Create/update/delete languages

### Concepts (Hierarchical)
- **Queries:** [concept.md](query/concept.md) - Concept hierarchy, children
- **Mutations:** [concept.md](mutation/concept.md) - Create/update/delete concepts

### Dictionaries (Translations)
- **Queries:** [dictionary.md](query/dictionary.md) - Get translations
- **Mutations:** [dictionary.md](mutation/dictionary.md) - Create/update/delete translations

### File Uploads
- **Queries:** [file.md](query/file.md) - List my files
- **Mutations:** [file.md](mutation/file.md) - Upload/delete files

### Search
- **Queries:** [search.md](query/search.md) - Full-text search, suggestions

### Audit Logs
- **Queries:** [audit.md](query/audit.md) - View audit logs, user activity

### Soft Delete
- **Queries:** [soft_delete.md](query/soft_delete.md) - List deleted records
- **Mutations:** [soft_delete.md](mutation/soft_delete.md) - Restore/permanently delete

### Import/Export
- **Queries:** [import_export.md](query/import_export.md) - Job status
- **Mutations:** [import_export.md](mutation/import_export.md) - Export/import data

---

## GraphQL Playground Features

### Autocomplete
Press `Ctrl+Space` to see available fields and operations.

### Documentation
Click the "Docs" button on the right to explore the schema.

### Query Formatting
Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) to format your query.

### Multiple Operations
Use operation names to run specific operations:

```graphql
query GetUser {
  me { username }
}

mutation UpdateUser {
  updateProfile(firstName: "John") {
    id
  }
}
```

### Variables
Define variables in the "QUERY VARIABLES" panel:

```graphql
mutation Login($username: String!, $password: String!) {
  login(input: {
    username: $username
    password: $password
  }) {
    accessToken
  }
}
```

```json
{
  "username": "admin",
  "password": "Admin123!"
}
```

---

## Test Accounts

Available when `SEED_DATABASE=true`:
- `admin / Admin123!` - Full access
- `moderator / Moderator123!` - User management
- `editor / Editor123!` - Content management
- `testuser / User123!` - Regular user

---

## Error Handling

GraphQL returns errors in standardized format:

```json
{
  "data": null,
  "errors": [
    {
      "message": "Not authenticated",
      "locations": [{"line": 2, "column": 3}],
      "path": ["me"]
    }
  ]
}
```

Common error messages:
- `Not authenticated` - Missing or invalid access token
- `Invalid credentials` - Wrong username/password
- `Permission denied` - Insufficient permissions
- `Not found` - Entity doesn't exist
- `Validation error` - Invalid input data

---

## See Also

- **[CLAUDE.md](../../CLAUDE.md)** - Full project documentation
- **[DEPLOYMENT.md](../../DEPLOYMENT.md)** - Deployment guide
- **[OAUTH_SETUP.md](../OAUTH_SETUP.md)** - OAuth configuration
- **[IMPORT_EXPORT.md](../IMPORT_EXPORT.md)** - Import/export guide
