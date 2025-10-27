"""
GraphQL schemas for Admin operations.

Provides admin-only queries and mutations for user management and system stats.
"""

from typing import List, Optional
import strawberry
from strawberry.types import Info

from auth.services.admin_service import AdminService
from auth.services.permission_service import PermissionService
from core.services.audit_service import AuditService
from auth.dependencies.auth import get_required_user
from auth.models.user import UserModel

# ============================================================================
# Types
# ============================================================================

@strawberry.type(description="User statistics for the admin dashboard.")
class UserStats:
    total: int = strawberry.field(description="Total number of users.")
    active: int = strawberry.field(description="Number of active users.")
    verified: int = strawberry.field(description="Number of users with verified emails.")
    new_last_30_days: int = strawberry.field(description="Number of new users in the last 30 days.")
    banned: int = strawberry.field(description="Number of banned users.")

@strawberry.type(description="Content statistics for the admin dashboard.")
class ContentStats:
    concepts: int = strawberry.field(description="Total number of concepts.")
    dictionaries: int = strawberry.field(description="Total number of dictionary entries (translations).")
    languages: int = strawberry.field(description="Total number of languages.")

@strawberry.type(description="File storage statistics.")
class FileStats:
    total: int = strawberry.field(description="Total number of uploaded files.")
    total_size_bytes: int = strawberry.field(description="Total size of all files in bytes.")
    total_size_mb: float = strawberry.field(description="Total size of all files in megabytes.")

@strawberry.type(description="Audit log statistics.")
class AuditStats:
    total_logs: int = strawberry.field(description="Total number of audit log entries.")
    logs_last_30_days: int = strawberry.field(description="Number of audit log entries in the last 30 days.")

@strawberry.type(description="A comprehensive overview of system statistics.")
class SystemStats:
    users: UserStats = strawberry.field(description="User-related statistics.")
    content: ContentStats = strawberry.field(description="Content-related statistics.")
    files: FileStats = strawberry.field(description="File storage statistics.")
    audit: AuditStats = strawberry.field(description="Audit log statistics.")
    roles: strawberry.scalars.JSON = strawberry.field(description="JSON object showing user distribution by role.")

@strawberry.type(description="Detailed user information for admin purposes.")
class AdminUser:
    id: int
    username: str
    email: str
    is_active: bool
    is_verified: bool
    created_at: str
    updated_at: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    roles: List[str] = strawberry.field(description="List of roles assigned to the user.")

@strawberry.type(description="Paginated response for the list of all users.")
class AllUsersResponse:
    users: List[AdminUser]
    total: int = strawberry.field(description="Total number of users matching the filters.")
    has_more: bool = strawberry.field(description="Indicates if more pages are available.")

@strawberry.type(description="Standard result for bulk operations.")
class BulkOperationResult:
    success: bool
    count: int = strawberry.field(description="Number of items affected.")
    message: str

# ============================================================================
# Inputs
# ============================================================================

@strawberry.input(description="Filters for querying the list of all users.")
class UserFilters:
    is_active: Optional[bool] = strawberry.field(default=None, description="Filter by active status.")
    is_verified: Optional[bool] = strawberry.field(default=None, description="Filter by email verification status.")
    role_name: Optional[str] = strawberry.field(default=None, description="Filter by a specific role name.")
    search: Optional[str] = strawberry.field(default=None, description="Search by username, email, or name.")

# ============================================================================
# Queries
# ============================================================================

@strawberry.type
class AdminQuery:
    """Admin-only queries for system management."""

    @strawberry.field(description="""Get a paginated list of all users with advanced filtering.

**Required permissions:** `admin:read:users`

Example:
```graphql
query GetAllUsers {
  allUsers(limit: 20, filters: { isActive: true, roleName: "editor", search: "john" }) {
    users {
      id
      username
      email
      isActive
      roles
    }
    total
    hasMore
  }
}
```
""")
    async def all_users(
        self, info: Info, limit: int = 50, offset: int = 0, filters: Optional[UserFilters] = None
    ) -> AllUsersResponse:
        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(user, "admin", "read", "users"):
            raise Exception("Permission denied: admin:read:users required")

        kwargs = filters.__dict__ if filters else {}
        users, total = AdminService.get_all_users(db, limit=limit, offset=offset, **kwargs)

        admin_users = [
            AdminUser(
                id=u.id, username=u.username, email=u.email, is_active=u.is_active,
                is_verified=u.is_verified, created_at=u.created_at.isoformat(),
                updated_at=u.updated_at.isoformat() if u.updated_at else None,
                first_name=u.profile.first_name if u.profile else None,
                last_name=u.profile.last_name if u.profile else None,
                roles=[ur.role.name for ur in u.roles if ur.role]
            )
            for u in users
        ]

        return AllUsersResponse(users=admin_users, total=total, has_more=(offset + len(users)) < total)

    @strawberry.field(description="""Get a comprehensive dashboard of system statistics.

**Required permissions:** `admin:read:system`

Example:
```graphql
query GetSystemStats {
  systemStats {
    users { total active verified newLast30Days banned }
    content { concepts dictionaries languages }
    files { total totalSizeBytes totalSizeMb }
    audit { totalLogs logsLast30Days }
    roles
  }
}
```
""")
    async def system_stats(self, info: Info) -> SystemStats:
        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(user, "admin", "read", "system"):
            raise Exception("Permission denied: admin:read:system required")

        stats = AdminService.get_system_stats(db)
        return SystemStats(
            users=UserStats(**stats["users"]),
            content=ContentStats(**stats["content"]),
            files=FileStats(total=stats["files"]["total"], total_size_bytes=stats["files"]["total_size_bytes"], total_size_mb=stats["files"]["total_size_mb"]),
            audit=AuditStats(**stats["audit"]),
            roles=stats["roles"]
        )

# ============================================================================
# Mutations
# ============================================================================

@strawberry.type
class AdminMutation:
    """Admin-only mutations for system management."""

    @strawberry.mutation(description="""Bans a user, setting their `isActive` status to `false`.

**Required permissions:** `admin:update:users`

Example:
```graphql
mutation BanUser {
  banUser(userId: 123, reason: "Spam and abuse") {
    id
    username
    isActive  # will be false
  }
}
```
""")
    async def ban_user(self, info: Info, user_id: int, reason: Optional[str] = None) -> AdminUser:
        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        admin_user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(admin_user, "admin", "update", "users"):
            raise Exception("Permission denied: admin:update:users required")

        user = AdminService.ban_user(db, user_id, admin_user, reason)
        AuditService(db).log(
            user_id=admin_user.id, action="ban_user", entity_type="user", entity_id=user_id,
            description=f"Banned user {user.username}. Reason: {reason}", status="success",
            ip_address=info.context["request"].client.host, user_agent=info.context["request"].headers.get("user-agent")
        )

        return AdminUser(
            id=user.id, username=user.username, email=user.email, is_active=user.is_active,
            is_verified=user.is_verified, created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat() if user.updated_at else None,
            first_name=user.profile.first_name if user.profile else None,
            last_name=user.profile.last_name if user.profile else None,
            roles=[ur.role.name for ur in user.roles if ur.role]
        )

    @strawberry.mutation(description="""Unbans a user, setting their `isActive` status to `true`.

**Required permissions:** `admin:update:users`

Example:
```graphql
mutation UnbanUser {
  unbanUser(userId: 123) {
    id
    username
    isActive  # will be true
  }
}
```
""")
    async def unban_user(self, info: Info, user_id: int) -> AdminUser:
        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        admin_user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(admin_user, "admin", "update", "users"):
            raise Exception("Permission denied: admin:update:users required")

        user = AdminService.unban_user(db, user_id, admin_user)
        AuditService(db).log(
            user_id=admin_user.id, action="unban_user", entity_type="user", entity_id=user_id,
            description=f"Unbanned user {user.username}", status="success",
            ip_address=info.context["request"].client.host, user_agent=info.context["request"].headers.get("user-agent")
        )

        return AdminUser(
            id=user.id, username=user.username, email=user.email, is_active=user.is_active,
            is_verified=user.is_verified, created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat() if user.updated_at else None,
            first_name=user.profile.first_name if user.profile else None,
            last_name=user.profile.last_name if user.profile else None,
            roles=[ur.role.name for ur in user.roles if ur.role]
        )

    @strawberry.mutation(description="""Permanently deletes a user from the database. This action is irreversible.

**Required permissions:** `admin:delete:users`

**WARNING:** This is a hard delete and cannot be undone. Prefer banning or soft-deleting.

Example:
```graphql
mutation DeleteUserPermanently {
  deleteUserPermanently(userId: 123)
}
```
""")
    async def delete_user_permanently(self, info: Info, user_id: int) -> bool:
        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        admin_user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(admin_user, "admin", "delete", "users"):
            raise Exception("Permission denied: admin:delete:users required")

        target_user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not target_user:
            raise ValueError(f"User with ID {user_id} not found")
        username = target_user.username

        result = AdminService.delete_user_permanently(db, user_id, admin_user)
        AuditService(db).log(
            user_id=admin_user.id, action="delete_user_permanently", entity_type="user", entity_id=user_id,
            description=f"Permanently deleted user {username}", status="success",
            ip_address=info.context["request"].client.host, user_agent=info.context["request"].headers.get("user-agent")
        )
        return result

    @strawberry.mutation(description="""Assigns a role to multiple users at once.

**Required permissions:** `admin:update:users`

Example:
```graphql
mutation BulkAssignRole {
  bulkAssignRole(userIds: [10, 20, 30], roleName: "editor") {
    success
    count
    message
  }
}
```
""")
    async def bulk_assign_role(self, info: Info, user_ids: List[int], role_name: str) -> BulkOperationResult:
        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        admin_user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(admin_user, "admin", "update", "users"):
            raise Exception("Permission denied: admin:update:users required")

        count = AdminService.bulk_assign_role(db, user_ids, role_name, admin_user)
        AuditService(db).log(
            user_id=admin_user.id, action="bulk_assign_role", entity_type="role",
            description=f"Assigned role '{role_name}' to {count} users", status="success",
            ip_address=info.context["request"].client.host, user_agent=info.context["request"].headers.get("user-agent")
        )
        return BulkOperationResult(success=True, count=count, message=f"Assigned role '{role_name}' to {count} users")

    @strawberry.mutation(description="""Removes a role from multiple users at once.

**Required permissions:** `admin:update:users`

Example:
```graphql
mutation BulkRemoveRole {
  bulkRemoveRole(userIds: [10, 20, 30], roleName: "editor") {
    success
    count
    message
  }
}
```
""")
    async def bulk_remove_role(self, info: Info, user_ids: List[int], role_name: str) -> BulkOperationResult:
        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        admin_user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(admin_user, "admin", "update", "users"):
            raise Exception("Permission denied: admin:update:users required")

        count = AdminService.bulk_remove_role(db, user_ids, role_name, admin_user)
        AuditService(db).log(
            user_id=admin_user.id, action="bulk_remove_role", entity_type="role",
            description=f"Removed role '{role_name}' from {count} users", status="success",
            ip_address=info.context["request"].client.host, user_agent=info.context["request"].headers.get("user-agent")
        )
        return BulkOperationResult(success=True, count=count, message=f"Removed role '{role_name}' from {count} users")
