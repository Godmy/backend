"""
GraphQL schemas for Admin operations.

Provides admin-only queries and mutations for user management and system stats.

Implementation for User Story #8 - Admin Panel Features (P1)
"""

from typing import List, Optional
import strawberry
from strawberry.types import Info

from auth.services.admin_service import AdminService
from auth.services.permission_service import PermissionService
from core.services.audit_service import AuditService
from auth.dependencies.auth import get_required_user
from auth.models.user import UserModel
from core.database import get_db


# ============================================================================
# Types
# ============================================================================

@strawberry.type
class UserStats:
    """User statistics."""
    total: int
    active: int
    verified: int
    new_last_30_days: int
    banned: int


@strawberry.type
class ContentStats:
    """Content statistics."""
    concepts: int
    dictionaries: int
    languages: int


@strawberry.type
class FileStats:
    """File statistics."""
    total: int
    total_size_bytes: int
    total_size_mb: float


@strawberry.type
class AuditStats:
    """Audit log statistics."""
    total_logs: int
    logs_last_30_days: int


@strawberry.type
class SystemStats:
    """System statistics."""
    users: UserStats
    content: ContentStats
    files: FileStats
    audit: AuditStats
    roles: strawberry.scalars.JSON


@strawberry.type
class AdminUser:
    """User type for admin queries (includes more fields)."""
    id: int
    username: str
    email: str
    is_active: bool
    is_verified: bool
    created_at: str
    updated_at: Optional[str]

    # Profile fields
    first_name: Optional[str]
    last_name: Optional[str]

    # Role names
    roles: List[str]


@strawberry.type
class AllUsersResponse:
    """Response for allUsers query with pagination."""
    users: List[AdminUser]
    total: int
    has_more: bool


@strawberry.type
class BulkOperationResult:
    """Result of bulk operation."""
    success: bool
    count: int
    message: str


# ============================================================================
# Inputs
# ============================================================================

@strawberry.input
class UserFilters:
    """Filters for allUsers query."""
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role_name: Optional[str] = None
    search: Optional[str] = None


# ============================================================================
# Queries
# ============================================================================

@strawberry.type
class AdminQuery:
    """Admin queries (admin-only)."""

    @strawberry.field
    async def all_users(
        self,
        info: Info,
        limit: int = 50,
        offset: int = 0,
        filters: Optional[UserFilters] = None
    ) -> AllUsersResponse:
        """
        Get all users with filters and pagination (admin only).

        Args:
            limit: Max results (max 100)
            offset: Offset for pagination
            filters: Filter criteria

        Returns:
            Paginated list of users

        Example:
            query {
              allUsers(limit: 20, filters: { isActive: true, roleName: "admin" }) {
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
        """
        # Check admin permission
        current_user_dict = await get_required_user(info)
        db = next(get_db())

        user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(user, "admin", "read", "users"):
            raise Exception("Admin permission required")

        # Get filters
        kwargs = {}
        if filters:
            if filters.is_active is not None:
                kwargs["is_active"] = filters.is_active
            if filters.is_verified is not None:
                kwargs["is_verified"] = filters.is_verified
            if filters.role_name:
                kwargs["role_name"] = filters.role_name
            if filters.search:
                kwargs["search"] = filters.search

        # Get users
        users, total = AdminService.get_all_users(
            db,
            limit=limit,
            offset=offset,
            **kwargs
        )

        # Convert to AdminUser type
        admin_users = []
        for u in users:
            role_names = [ur.role.name for ur in u.roles if ur.role]
            admin_users.append(
                AdminUser(
                    id=u.id,
                    username=u.username,
                    email=u.email,
                    is_active=u.is_active,
                    is_verified=u.is_verified,
                    created_at=u.created_at.isoformat(),
                    updated_at=u.updated_at.isoformat() if u.updated_at else None,
                    first_name=u.profile.first_name if u.profile else None,
                    last_name=u.profile.last_name if u.profile else None,
                    roles=role_names
                )
            )

        return AllUsersResponse(
            users=admin_users,
            total=total,
            has_more=(offset + len(users)) < total
        )

    @strawberry.field
    async def system_stats(self, info: Info) -> SystemStats:
        """
        Get system statistics (admin only).

        Returns:
            System statistics

        Example:
            query {
              systemStats {
                users { total active verified }
                content { concepts dictionaries }
                files { total totalSizeMb }
              }
            }
        """
        # Check admin permission
        current_user_dict = await get_required_user(info)
        db = next(get_db())

        user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(user, "admin", "read", "system"):
            raise Exception("Admin permission required")

        # Get stats
        stats = AdminService.get_system_stats(db)

        return SystemStats(
            users=UserStats(**stats["users"]),
            content=ContentStats(**stats["content"]),
            files=FileStats(**stats["files"]),
            audit=AuditStats(**stats["audit"]),
            roles=stats["roles"]
        )


# ============================================================================
# Mutations
# ============================================================================

@strawberry.type
class AdminMutation:
    """Admin mutations (admin-only)."""

    @strawberry.mutation
    async def ban_user(
        self,
        info: Info,
        user_id: int,
        reason: Optional[str] = None
    ) -> AdminUser:
        """
        Ban a user (set is_active=False).

        Args:
            user_id: ID of user to ban
            reason: Optional reason for ban

        Returns:
            Updated user

        Example:
            mutation {
              banUser(userId: 123, reason: "Spam") {
                id
                username
                isActive
              }
            }
        """
        # Check admin permission
        current_user_dict = await get_required_user(info)
        db = next(get_db())

        admin_user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(admin_user, "admin", "update", "users"):
            raise Exception("Admin permission required")

        # Ban user
        user = AdminService.ban_user(db, user_id, admin_user, reason)

        # Log action
        audit_service = AuditService(db)
        audit_service.log(
            user_id=admin_user.id,
            action="ban_user",
            entity_type="user",
            entity_id=user_id,
            description=f"Banned user {user.username}. Reason: {reason}",
            status="success",
            ip_address=info.context["request"].client.host,
            user_agent=info.context["request"].headers.get("user-agent")
        )

        # Return
        role_names = [ur.role.name for ur in user.roles if ur.role]
        return AdminUser(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat() if user.updated_at else None,
            first_name=user.profile.first_name if user.profile else None,
            last_name=user.profile.last_name if user.profile else None,
            roles=role_names
        )

    @strawberry.mutation
    async def unban_user(self, info: Info, user_id: int) -> AdminUser:
        """
        Unban a user (set is_active=True).

        Args:
            user_id: ID of user to unban

        Returns:
            Updated user

        Example:
            mutation {
              unbanUser(userId: 123) {
                id
                username
                isActive
              }
            }
        """
        # Check admin permission
        current_user_dict = await get_required_user(info)
        db = next(get_db())

        admin_user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(admin_user, "admin", "update", "users"):
            raise Exception("Admin permission required")

        # Unban user
        user = AdminService.unban_user(db, user_id, admin_user)

        # Log action
        audit_service = AuditService(db)
        audit_service.log(
            user_id=admin_user.id,
            action="unban_user",
            entity_type="user",
            entity_id=user_id,
            description=f"Unbanned user {user.username}",
            status="success",
            ip_address=info.context["request"].client.host,
            user_agent=info.context["request"].headers.get("user-agent")
        )

        # Return
        role_names = [ur.role.name for ur in user.roles if ur.role]
        return AdminUser(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat() if user.updated_at else None,
            first_name=user.profile.first_name if user.profile else None,
            last_name=user.profile.last_name if user.profile else None,
            roles=role_names
        )

    @strawberry.mutation
    async def delete_user_permanently(self, info: Info, user_id: int) -> bool:
        """
        Permanently delete a user (hard delete).

        WARNING: This is irreversible!

        Args:
            user_id: ID of user to delete

        Returns:
            True if deleted

        Example:
            mutation {
              deleteUserPermanently(userId: 123)
            }
        """
        # Check admin permission
        current_user_dict = await get_required_user(info)
        db = next(get_db())

        admin_user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(admin_user, "admin", "delete", "users"):
            raise Exception("Admin permission required")

        # Get user info before deletion (for audit log)
        target_user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if target_user:
            username = target_user.username
        else:
            raise ValueError(f"User with ID {user_id} not found")

        # Delete user
        result = AdminService.delete_user_permanently(db, user_id, admin_user)

        # Log action
        audit_service = AuditService(db)
        audit_service.log(
            user_id=admin_user.id,
            action="delete_user_permanently",
            entity_type="user",
            entity_id=user_id,
            description=f"Permanently deleted user {username}",
            status="success",
            ip_address=info.context["request"].client.host,
            user_agent=info.context["request"].headers.get("user-agent")
        )

        return result

    @strawberry.mutation
    async def bulk_assign_role(
        self,
        info: Info,
        user_ids: List[int],
        role_name: str
    ) -> BulkOperationResult:
        """
        Assign role to multiple users.

        Args:
            user_ids: List of user IDs
            role_name: Role name to assign

        Returns:
            Result with count of users updated

        Example:
            mutation {
              bulkAssignRole(userIds: [1, 2, 3], roleName: "editor") {
                success
                count
                message
              }
            }
        """
        # Check admin permission
        current_user_dict = await get_required_user(info)
        db = next(get_db())

        admin_user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(admin_user, "admin", "update", "users"):
            raise Exception("Admin permission required")

        # Assign role
        count = AdminService.bulk_assign_role(db, user_ids, role_name, admin_user)

        # Log action
        audit_service = AuditService(db)
        audit_service.log(
            user_id=admin_user.id,
            action="bulk_assign_role",
            entity_type="role",
            description=f"Assigned role {role_name} to {count} users",
            status="success",
            ip_address=info.context["request"].client.host,
            user_agent=info.context["request"].headers.get("user-agent")
        )

        return BulkOperationResult(
            success=True,
            count=count,
            message=f"Assigned role {role_name} to {count} users"
        )

    @strawberry.mutation
    async def bulk_remove_role(
        self,
        info: Info,
        user_ids: List[int],
        role_name: str
    ) -> BulkOperationResult:
        """
        Remove role from multiple users.

        Args:
            user_ids: List of user IDs
            role_name: Role name to remove

        Returns:
            Result with count of users updated

        Example:
            mutation {
              bulkRemoveRole(userIds: [1, 2, 3], roleName: "editor") {
                success
                count
                message
              }
            }
        """
        # Check admin permission
        current_user_dict = await get_required_user(info)
        db = next(get_db())

        admin_user = db.query(UserModel).filter(UserModel.id == current_user_dict["id"]).first()
        if not PermissionService.check_permission(admin_user, "admin", "update", "users"):
            raise Exception("Admin permission required")

        # Remove role
        count = AdminService.bulk_remove_role(db, user_ids, role_name, admin_user)

        # Log action
        audit_service = AuditService(db)
        audit_service.log(
            user_id=admin_user.id,
            action="bulk_remove_role",
            entity_type="role",
            description=f"Removed role {role_name} from {count} users",
            status="success",
            ip_address=info.context["request"].client.host,
            user_agent=info.context["request"].headers.get("user-agent")
        )

        return BulkOperationResult(
            success=True,
            count=count,
            message=f"Removed role {role_name} from {count} users"
        )
