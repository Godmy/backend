'''"""
GraphQL schemas for viewing audit logs.
"""

from datetime import datetime
from typing import List, Optional
import strawberry
from sqlalchemy.orm import Session
from strawberry.types import Info

from core.models.audit_log import AuditLog as AuditLogModel
from core.services.audit_service import AuditService
from auth.services.permission_service import PermissionService
from auth.models.user import UserModel

# ============================================================================
# Types
# ============================================================================

@strawberry.type(description="Represents a single audit log entry.")
class AuditLogType:
    id: int
    user_id: Optional[int] = strawberry.field(description="The ID of the user who performed the action.")
    action: str = strawberry.field(description="The type of action performed (e.g., 'login', 'create_concept').")
    entity_type: Optional[str] = strawberry.field(description="The type of entity that was affected (e.g., 'user', 'concept').")
    entity_id: Optional[int] = strawberry.field(description="The ID of the entity that was affected.")
    old_data: Optional[strawberry.scalars.JSON] = strawberry.field(description="A JSON snapshot of the data before the change.")
    new_data: Optional[strawberry.scalars.JSON] = strawberry.field(description="A JSON snapshot of the data after the change.")
    ip_address: Optional[str] = strawberry.field(description="The IP address of the client.")
    user_agent: Optional[str] = strawberry.field(description="The User-Agent string of the client.")
    description: Optional[str] = strawberry.field(description="A human-readable description of the action.")
    status: str = strawberry.field(description="The status of the action (e.g., 'success', 'failure').")
    created_at: datetime = strawberry.field(description="The timestamp of when the action occurred.")

    @staticmethod
    def from_model(log: AuditLogModel) -> "AuditLogType":
        return AuditLogType(
            id=log.id, user_id=log.user_id, action=log.action, entity_type=log.entity_type,
            entity_id=log.entity_id, old_data=log.old_data, new_data=log.new_data,
            ip_address=log.ip_address, user_agent=log.user_agent,
            description=log.description or log.action_description, status=log.status,
            created_at=log.created_at
        )

@strawberry.type(description="A paginated list of audit logs.")
class AuditLogsPaginated:
    logs: List[AuditLogType]
    total: int = strawberry.field(description="Total number of logs matching the filters.")
    has_more: bool = strawberry.field(description="Indicates if more pages are available.")

@strawberry.type(description="A summary of user activity by action type.")
class UserActivityType:
    action: str = strawberry.field(description="The action type.")
    count: int = strawberry.field(description="The number of times the action was performed.")

# ============================================================================
# Inputs
# ============================================================================

@strawberry.input(description="Filters for querying audit logs.")
class AuditLogsFilterInput:
    user_id: Optional[int] = strawberry.field(default=None, description="Filter by user ID.")
    action: Optional[str] = strawberry.field(default=None, description="Filter by action type (e.g., 'login').")
    entity_type: Optional[str] = strawberry.field(default=None, description="Filter by entity type (e.g., 'concept').")
    entity_id: Optional[int] = strawberry.field(default=None, description="Filter by entity ID.")
    status: Optional[str] = strawberry.field(default=None, description="Filter by status ('success' or 'failure').")
    from_date: Optional[datetime] = strawberry.field(default=None, description="Start of the date range (ISO 8601 format).")
    to_date: Optional[datetime] = strawberry.field(default=None, description="End of the date range (ISO 8601 format).")

# ============================================================================
# Queries
# ============================================================================

@strawberry.type
class AuditLogQuery:
    """GraphQL queries for viewing audit logs."""

    @strawberry.field(description='''Get a paginated list of all audit logs with advanced filtering.

**Required permissions:** `admin:read:system`

Example:
```graphql
query GetAuditLogs {
  auditLogs(filters: { userId: 1, action: "login", status: "success" }, limit: 50) {
    logs {
      id
      action
      ipAddress
      createdAt
    }
    total
  }
}
```
''')
    def audit_logs(
        self, info: Info, filters: Optional[AuditLogsFilterInput] = None, limit: int = 100, offset: int = 0
    ) -> AuditLogsPaginated:
        user_dict = info.context.get("user")
        if not user_dict:
            raise Exception("Authentication required")

        db: Session = info.context["db"]
        user = db.query(UserModel).filter(UserModel.id == user_dict["id"]).first()
        if not PermissionService.check_permission(user, "admin", "read", "system"):
            raise Exception("Admin privileges required")

        service = AuditService(db)
        kwargs = {"limit": limit, "offset": offset, **(filters.__dict__ if filters else {})}
        
        logs, total = service.get_logs(**kwargs)
        return AuditLogsPaginated(
            logs=[AuditLogType.from_model(log) for log in logs],
            total=total,
            has_more=(offset + limit) < total,
        )

    @strawberry.field(description='''Get a paginated list of the current user\'s own audit logs.

Example:
```graphql
query GetMyLogs {
  myAuditLogs(action: "logout", limit: 10) {
    logs {
      id
      action
      createdAt
    }
  }
}
```
''')
    def my_audit_logs(
        self, info: Info, action: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> AuditLogsPaginated:
        user_dict = info.context.get("user")
        if not user_dict:
            raise Exception("Authentication required")

        db: Session = info.context["db"]
        service = AuditService(db)
        logs, total = service.get_logs(user_id=user_dict[\'id\'], action=action, limit=limit, offset=offset)

        return AuditLogsPaginated(
            logs=[AuditLogType.from_model(log) for log in logs],
            total=total,
            has_more=(offset + limit) < total,
        )

    @strawberry.field(description='''Get activity statistics for a specific user, grouped by action type.

If `userId` is not provided, returns stats for the current user. Requires admin privileges to view other users\' stats.

**Required permissions (for other users):** `admin:read:users`

Example:
```graphql
query GetUserActivity {
  userActivity(userId: 123, days: 30) {
    action
    count
  }
}
```
''')
    def user_activity(
        self, info: Info, user_id: Optional[int] = None, days: int = 30
    ) -> List[UserActivityType]:
        user_dict = info.context.get("user")
        if not user_dict:
            raise Exception("Authentication required")

        target_user_id = user_id if user_id is not None else user_dict[\'id\']
        
        db: Session = info.context["db"]
        if target_user_id != user_dict[\'id\']:
            user = db.query(UserModel).filter(UserModel.id == user_dict["id"]).first()
            if not PermissionService.check_permission(user, "admin", "read", "users"):
                raise Exception("Admin privileges required to view other users\' activity")

        service = AuditService(db)
        activity = service.get_user_activity(target_user_id, days)
        return [UserActivityType(action=item["action"], count=item["count"]) for item in activity]
'''
