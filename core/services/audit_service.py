"""
Сервис для аудит логирования
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from core.models.audit_log import AuditLog


class AuditService:
    """Сервис для работы с аудит логами"""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        action: str,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "success",
    ) -> AuditLog:
        """
        Создание записи в аудит логе

        Args:
            action: Тип действия (login, logout, create, update, delete, etc.)
            user_id: ID пользователя (None для system actions)
            entity_type: Тип сущности (user, concept, dictionary, file)
            entity_id: ID сущности
            old_data: Данные до изменения
            new_data: Данные после изменения
            ip_address: IP адрес пользователя
            user_agent: User Agent браузера
            description: Дополнительное описание
            status: Статус (success, failure, error)

        Returns:
            Созданная запись AuditLog
        """
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_data=old_data,
            new_data=new_data,
            ip_address=ip_address,
            user_agent=user_agent,
            description=description,
            status=status,
        )

        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)

        return audit_log

    def log_login(
        self,
        user_id: int,
        method: str = "password",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
    ) -> AuditLog:
        """Логирование входа"""
        return self.log(
            action="oauth_login" if method != "password" else "login",
            user_id=user_id,
            description=f"Login via {method}",
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
        )

    def log_register(
        self,
        user_id: int,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Логирование регистрации"""
        return self.log(
            action="register",
            user_id=user_id,
            new_data={"email": email},
            description=f"User registered with email {email}",
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def log_logout(
        self,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Логирование выхода"""
        return self.log(
            action="logout",
            user_id=user_id,
            description="User logged out",
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def log_entity_create(
        self,
        user_id: int,
        entity_type: str,
        entity_id: int,
        data: Dict[str, Any],
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Логирование создания сущности"""
        return self.log(
            action="create",
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            new_data=data,
            description=f"Created {entity_type} #{entity_id}",
            ip_address=ip_address,
        )

    def log_entity_update(
        self,
        user_id: int,
        entity_type: str,
        entity_id: int,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Логирование обновления сущности"""
        return self.log(
            action="update",
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            old_data=old_data,
            new_data=new_data,
            description=f"Updated {entity_type} #{entity_id}",
            ip_address=ip_address,
        )

    def log_entity_delete(
        self,
        user_id: int,
        entity_type: str,
        entity_id: int,
        data: Dict[str, Any],
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Логирование удаления сущности"""
        return self.log(
            action="delete",
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            old_data=data,
            description=f"Deleted {entity_type} #{entity_id}",
            ip_address=ip_address,
        )

    def get_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[AuditLog], int]:
        """
        Получение логов с фильтрацией

        Returns:
            Tuple[logs, total_count]
        """
        query = self.db.query(AuditLog)

        # Фильтры
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)

        if action:
            query = query.filter(AuditLog.action == action)

        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)

        if entity_id is not None:
            query = query.filter(AuditLog.entity_id == entity_id)

        if status:
            query = query.filter(AuditLog.status == status)

        if from_date:
            query = query.filter(AuditLog.created_at >= from_date)

        if to_date:
            query = query.filter(AuditLog.created_at <= to_date)

        # Подсчет total
        total = query.count()

        # Сортировка и пагинация
        logs = (
            query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
        )

        return logs, total

    def cleanup_old_logs(self, days: int = 365) -> int:
        """
        Удаление старых логов

        Args:
            days: Удалить логи старше N дней

        Returns:
            Количество удаленных записей
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = (
            self.db.query(AuditLog)
            .filter(AuditLog.created_at < cutoff_date)
            .delete(synchronize_session=False)
        )

        self.db.commit()
        return deleted

    def get_user_activity(
        self, user_id: int, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Получение статистики активности пользователя

        Returns:
            Список действий с количеством
        """
        from_date = datetime.utcnow() - timedelta(days=days)

        from sqlalchemy import func

        results = (
            self.db.query(
                AuditLog.action,
                func.count(AuditLog.id).label("count"),
            )
            .filter(AuditLog.user_id == user_id)
            .filter(AuditLog.created_at >= from_date)
            .group_by(AuditLog.action)
            .all()
        )

        return [{"action": r.action, "count": r.count} for r in results]
