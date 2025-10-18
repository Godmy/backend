"""
GraphQL схемы для аудит логов
"""
import strawberry
from typing import Optional, List
from datetime import datetime
from strawberry.types import Info
from sqlalchemy.orm import Session
from core.services.audit_service import AuditService
from core.models.audit_log import AuditLog as AuditLogModel


@strawberry.type
class AuditLogType:
    """GraphQL тип для аудит лога"""

    id: int
    user_id: Optional[int]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    old_data: Optional[str]  # JSON as string
    new_data: Optional[str]  # JSON as string
    ip_address: Optional[str]
    user_agent: Optional[str]
    description: Optional[str]
    status: str
    created_at: str

    @staticmethod
    def from_model(log: AuditLogModel) -> "AuditLogType":
        """Создание из модели"""
        import json

        return AuditLogType(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            old_data=json.dumps(log.old_data) if log.old_data else None,
            new_data=json.dumps(log.new_data) if log.new_data else None,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            description=log.description or log.action_description,
            status=log.status,
            created_at=log.created_at.isoformat(),
        )


@strawberry.type
class AuditLogsPaginated:
    """Пагинированный список аудит логов"""

    logs: List[AuditLogType]
    total: int
    has_more: bool


@strawberry.type
class UserActivityType:
    """Статистика активности пользователя"""

    action: str
    count: int


@strawberry.input
class AuditLogsFilterInput:
    """Фильтры для аудит логов"""

    user_id: Optional[int] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    status: Optional[str] = None
    from_date: Optional[str] = None  # ISO format
    to_date: Optional[str] = None  # ISO format


@strawberry.type
class AuditLogQuery:
    """GraphQL queries для аудит логов"""

    @strawberry.field
    def audit_logs(
        self,
        info: Info,
        filters: Optional[AuditLogsFilterInput] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AuditLogsPaginated:
        """Получить аудит логи (только для админов)"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")

        # Проверка прав админа
        if not self._is_admin(user):
            raise Exception("Admin privileges required")

        db: Session = info.context["db"]
        service = AuditService(db)

        # Парсинг фильтров
        kwargs = {"limit": limit, "offset": offset}

        if filters:
            if filters.user_id is not None:
                kwargs["user_id"] = filters.user_id
            if filters.action:
                kwargs["action"] = filters.action
            if filters.entity_type:
                kwargs["entity_type"] = filters.entity_type
            if filters.entity_id is not None:
                kwargs["entity_id"] = filters.entity_id
            if filters.status:
                kwargs["status"] = filters.status
            if filters.from_date:
                from datetime import datetime

                kwargs["from_date"] = datetime.fromisoformat(filters.from_date)
            if filters.to_date:
                from datetime import datetime

                kwargs["to_date"] = datetime.fromisoformat(filters.to_date)

        logs, total = service.get_logs(**kwargs)

        return AuditLogsPaginated(
            logs=[AuditLogType.from_model(log) for log in logs],
            total=total,
            has_more=(offset + limit) < total,
        )

    @strawberry.field
    def my_audit_logs(
        self,
        info: Info,
        action: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditLogsPaginated:
        """Получить мои аудит логи"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")

        db: Session = info.context["db"]
        service = AuditService(db)

        logs, total = service.get_logs(
            user_id=user.id, action=action, limit=limit, offset=offset
        )

        return AuditLogsPaginated(
            logs=[AuditLogType.from_model(log) for log in logs],
            total=total,
            has_more=(offset + limit) < total,
        )

    @strawberry.field
    def user_activity(
        self,
        info: Info,
        user_id: Optional[int] = None,
        days: int = 30,
    ) -> List[UserActivityType]:
        """Получить статистику активности пользователя"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")

        # Если user_id не указан, берем текущего пользователя
        target_user_id = user_id if user_id is not None else user.id

        # Если запрашиваем чужую статистику, нужны права админа
        if target_user_id != user.id and not self._is_admin(user):
            raise Exception("Admin privileges required")

        db: Session = info.context["db"]
        service = AuditService(db)

        activity = service.get_user_activity(target_user_id, days)

        return [
            UserActivityType(action=item["action"], count=item["count"])
            for item in activity
        ]

    def _is_admin(self, user) -> bool:
        """Проверка является ли пользователь админом"""
        for role in user.roles:
            if role.name == "admin":
                return True
        return False
