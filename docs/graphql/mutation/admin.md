# Admin Panel Mutations

**Required permissions:** `admin:update:users` or `admin:delete:users`

## Ban User

Ban a user (sets isActive to false).

```graphql
mutation BanUser {
  banUser(userId: 123, reason: "Spam and abuse") {
    id
    username
    isActive  # false
  }
}
```

**Audit logging:** Automatically logged with admin ID, reason, timestamp

---

## Unban User

Unban a previously banned user (sets isActive to true).

```graphql
mutation UnbanUser {
  unbanUser(userId: 123) {
    id
    username
    isActive  # true
  }
}
```

---

## Delete User Permanently

Permanently delete a user from the database (irreversible).

⚠️ **WARNING:** This action is irreversible! Use soft delete (via user profile) instead.

```graphql
mutation DeleteUserPermanently {
  deleteUserPermanently(userId: 123)  # Returns boolean
}
```

**Safety features:**
- Cannot delete yourself
- Requires admin permission
- All actions logged in audit trail

---

## Bulk Assign Role

Assign a role to multiple users at once.

```graphql
mutation BulkAssignRole {
  bulkAssignRole(userIds: [10, 20, 30], roleName: "editor") {
    success
    count  # Number of users updated
    message
  }
}
```

**Notes:**
- Skips invalid/not-found users
- Returns count of successfully updated users

---

## Bulk Remove Role

Remove a role from multiple users at once.

```graphql
mutation BulkRemoveRole {
  bulkRemoveRole(userIds: [10, 20, 30], roleName: "editor") {
    success
    count  # Number of users updated
    message
  }
}
```

---

## Use Cases

- Ban abusive users
- Bulk promote users to moderators
- View system health dashboard
- Search and filter users
- Audit admin actions
- Manage user roles at scale

---

## Implementation

- `auth/services/admin_service.py` - Business logic
- `auth/schemas/admin.py` - GraphQL API
- `core/schemas/schema.py` - Integration
- `tests/test_admin.py` - Test suite

**Audit logging:** All actions automatically logged with:
- Admin user ID
- Action performed
- Target entity
- Timestamp
- IP address and User-Agent
- Success/failure status
