# Authentication Queries

## Get Current User

Get information about the currently authenticated user.

**Required:** Authorization header with access token

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

**Expected response:**
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

**HTTP Headers:**
```json
{
  "Authorization": "Bearer YOUR_ACCESS_TOKEN_HERE"
}
```

## Test Accounts

Available test accounts (when `SEED_DATABASE=true`):
- `admin / Admin123!` - Full access
- `moderator / Moderator123!` - User management
- `editor / Editor123!` - Content management
- `testuser / User123!` - Regular user
