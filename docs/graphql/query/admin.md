# Admin Panel Queries

**Required permissions:** `admin:read:users` or `admin:read:system`

## Get All Users

Get list of all users with filtering and pagination.

```graphql
query GetAllUsers {
  allUsers(
    limit: 50
    offset: 0
    filters: {
      isActive: true
      isVerified: true
      roleName: "editor"
      search: "john"
    }
  ) {
    users {
      id
      username
      email
      isActive
      isVerified
      roles
      firstName
      lastName
      createdAt
    }
    total
    hasMore
  }
}
```

**Filter options:**
- `isActive` - Filter by active status
- `isVerified` - Filter by verification status
- `roleName` - Filter by role name
- `search` - Search by username, email, firstName, lastName

---

## Get System Statistics

Get comprehensive system statistics dashboard.

```graphql
query GetSystemStats {
  systemStats {
    users {
      total
      active
      verified
      newLast30Days
      banned
    }
    content {
      concepts
      dictionaries
      languages
    }
    files {
      total
      totalSizeMb
    }
    audit {
      totalLogs
      logsLast30Days
    }
    roles  # JSON object with role distribution
  }
}
```

---

## Implementation

- `auth/services/admin_service.py` - AdminService
- `auth/schemas/admin.py` - GraphQL API
- `tests/test_admin.py` - Test suite

**Security:**
- All actions logged in audit trail
- Only users with "admin" role have access
