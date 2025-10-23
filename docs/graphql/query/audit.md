# Audit Logging Queries

## View My Audit Logs

View your own audit logs.

**Required:** Authorization header

```graphql
query MyAuditLogs {
  myAuditLogs(action: "login", limit: 10) {
    logs {
      id
      action
      entityType
      entityId
      description
      status
      ipAddress
      createdAt
    }
    total
    hasMore
  }
}
```

**Filter options:**
- `action` - Filter by action type (login, logout, create, update, delete, etc.)
- `limit` - Max results per page
- `offset` - Pagination offset

---

## View All Audit Logs (Admin)

View all audit logs with advanced filtering.

**Required:** Admin permission (`admin:read:system`)

```graphql
query AuditLogs {
  auditLogs(
    filters: {
      userId: 123
      action: "login"
      entityType: "concept"
      status: "success"
      fromDate: "2025-01-01T00:00:00"
      toDate: "2025-12-31T23:59:59"
    }
    limit: 100
    offset: 0
  ) {
    logs {
      id
      userId
      action
      entityType
      entityId
      oldData
      newData
      description
      status
      ipAddress
      userAgent
      createdAt
    }
    total
    hasMore
  }
}
```

**Filter options:**
- `userId` - Filter by user ID
- `action` - Filter by action type
- `entityType` - Filter by entity (concept, user, dictionary, etc.)
- `status` - Filter by status (success, failure)
- `fromDate`, `toDate` - Date range filter

---

## Get User Activity Statistics

Get activity statistics for a specific user.

**Required:** Admin permission

```graphql
query UserActivity {
  userActivity(userId: 123, days: 30) {
    action
    count
  }
}
```

**Returns:** Array of action counts for the last N days

**Example response:**
```json
{
  "data": {
    "userActivity": [
      { "action": "login", "count": 45 },
      { "action": "create", "count": 12 },
      { "action": "update", "count": 8 }
    ]
  }
}
```

---

## Logged Actions

**Authentication events:**
- `login` - User login
- `logout` - User logout
- `register` - User registration
- `oauth_login` - OAuth authentication

**Profile events:**
- `password_change` - Password changed
- `email_change` - Email changed
- `password_reset` - Password reset
- `profile_update` - Profile updated

**Entity events:**
- `create` - Entity created
- `update` - Entity updated
- `delete` - Entity deleted

**File events:**
- `upload` - File uploaded

**Admin events:**
- `ban_user` - User banned
- `unban_user` - User unbanned
- `role_change` - User role changed
- `bulk_assign_role` - Bulk role assignment
- `bulk_remove_role` - Bulk role removal

---

## Audit Log Fields

- `id` - Unique identifier
- `userId` - User who performed action
- `action` - Action type
- `entityType` - Type of entity affected (optional)
- `entityId` - ID of entity affected (optional)
- `oldData` - JSON snapshot before change (optional)
- `newData` - JSON snapshot after change (optional)
- `description` - Human-readable description
- `status` - success or failure
- `ipAddress` - Client IP address
- `userAgent` - Client User-Agent
- `createdAt` - Timestamp

---

## Implementation

- `core/models/audit_log.py` - AuditLogModel
- `core/schemas/audit.py` - GraphQL API
- `core/services/audit_service.py` - AuditService

**Service methods:**
- `log()` - Generic logging
- `log_login()`, `log_logout()`, `log_register()` - Auth events
- `log_entity_create()`, `log_entity_update()`, `log_entity_delete()` - CRUD
- `get_logs()` - Retrieve with filters
- `get_user_activity()` - Statistics
- `cleanup_old_logs()` - Automatic cleanup
