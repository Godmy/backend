# GraphQL Mutations Documentation

This directory contains documentation for all GraphQL mutations organized by functional modules.

## Available Mutations

### Authentication
- **[auth.md](auth.md)** - Authentication mutations (register, login, refresh token, OAuth, password reset, email verification)

### User Profile
- **[profile.md](profile.md)** - Profile mutations (update profile, change password, change email, delete account)

### Admin Panel
- **[admin.md](admin.md)** - Admin mutations (ban/unban users, bulk role management, delete users)

### Languages
- **[language.md](language.md)** - Language mutations (create, update, delete)

### Concepts
- **[concept.md](concept.md)** - Concept mutations (create, update, delete hierarchy)

### Dictionaries (Translations)
- **[dictionary.md](dictionary.md)** - Translation mutations (create, update, delete translations)

### Files
- **[file.md](file.md)** - File mutations (upload avatar, upload file, delete file)

### Soft Delete
- **[soft_delete.md](soft_delete.md)** - Soft delete mutations (restore, permanent delete)

### Import/Export
- **[import_export.md](import_export.md)** - Import/export mutations (export data, import data)

---

## Using in GraphQL Playground

1. Open GraphQL Playground: http://localhost:8000/graphql
2. Add authorization header for protected mutations:
   ```json
   {
     "Authorization": "Bearer YOUR_ACCESS_TOKEN"
   }
   ```
3. Use autocomplete (Ctrl+Space) for field suggestions
4. View schema documentation in the "Docs" panel

---

## Example Mutation

```graphql
mutation RegisterNewUser {
  register(input: {
    username: "johndoe"
    email: "john@example.com"
    password: "SecurePass123!"
    firstName: "John"
    lastName: "Doe"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

**Then use the access token in subsequent requests:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## File Upload Example

For file uploads, use multipart form-data:

```graphql
mutation UploadAvatar($file: Upload!) {
  uploadAvatar(file: $file) {
    id
    url
    thumbnailUrl
  }
}
```

**Variables:**
```json
{
  "file": null
}
```

Then upload the file via the GraphQL Playground file input.

---

## See Also

- **[Queries](../query/README.md)** - GraphQL queries documentation
- **[CLAUDE.md](../../../CLAUDE.md)** - Full project documentation
