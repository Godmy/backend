# Admin Panel Features

Comprehensive admin panel with user management, system statistics, and bulk operations.

## Features

- User management (ban, unban, delete)
- Bulk role assignment/removal
- System statistics dashboard
- User filtering and search
- Audit logging for all admin actions
- Permission-based access control

## GraphQL API

- **Queries:** [docs/graphql/query/admin.md](../graphql/query/admin.md)
- **Mutations:** [docs/graphql/mutation/admin.md](../graphql/mutation/admin.md)

## Permission Requirements

- All admin queries require `admin:read:users` or `admin:read:system` permission
- All admin mutations require `admin:update:users` or `admin:delete:users` permission
- Only users with "admin" role have these permissions by default

## Audit Logging

All admin actions are automatically logged with:
- Admin user ID
- Action performed (ban_user, unban_user, bulk_assign_role, etc.)
- Target entity (user ID, role name)
- Timestamp
- IP address and User-Agent
- Success/failure status

## Safety Features

- Cannot ban/delete yourself
- Cannot delete users without admin permission
- All actions logged in audit trail
- Bulk operations skip invalid/not-found users
- Soft delete preferred over hard delete

## Implementation

- `auth/services/admin_service.py` - Business logic for all admin operations
- `auth/schemas/admin.py` - GraphQL API (queries and mutations)
- `core/schemas/schema.py` - Integration into main schema
- `tests/test_admin.py` - Comprehensive test suite

## Use Cases

- Ban abusive users
- Bulk promote users to moderators
- View system health dashboard
- Search and filter users
- Audit admin actions
- Manage user roles at scale
