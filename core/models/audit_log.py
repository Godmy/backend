"""
Модель для аудит логов
"""

from sqlalchemy import JSON, Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from core.models.base import BaseModel


class AuditLog(BaseModel):
    """Модель аудит лога для отслеживания действий пользователей"""

    __tablename__ = "audit_logs"

    # Пользователь, выполнивший действие (nullable для system actions)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Тип действия
    action = Column(String(50), nullable=False, index=True)
    # login, logout, register, create, update, delete, oauth_login, password_change, etc.

    # Связанная сущность
    entity_type = Column(String(50), nullable=True, index=True)  # user, concept, dictionary, file
    entity_id = Column(Integer, nullable=True, index=True)

    # Данные до изменения
    old_data = Column(JSON, nullable=True)

    # Данные после изменения
    new_data = Column(JSON, nullable=True)

    # Метаданные запроса
    ip_address = Column(String(45), nullable=True)  # IPv4 или IPv6
    user_agent = Column(Text, nullable=True)

    # Дополнительная информация
    description = Column(Text, nullable=True)
    status = Column(String(20), default="success", index=True)  # success, failure, error

    # Composite indexes for common audit log queries
    __table_args__ = (
        # Index for filtering by entity
        Index('ix_audit_logs_entity', 'entity_type', 'entity_id'),
        # Index for user activity timeline
        Index('ix_audit_logs_user_created', 'user_id', 'created_at'),
        # Index for recent actions by type
        Index('ix_audit_logs_action_created', 'action', 'created_at'),
        # Index for failed actions analysis
        Index('ix_audit_logs_status_created', 'status', 'created_at'),
    )

    # Relationships
    user = relationship("UserModel", backref="audit_logs", foreign_keys=[user_id])

    def __repr__(self):
        return f"<AuditLog {self.action} by user_id={self.user_id}>"

    @property
    def action_description(self):
        """Человеко-читаемое описание действия"""
        descriptions = {
            "login": "User logged in",
            "logout": "User logged out",
            "register": "User registered",
            "oauth_login": "User logged in via OAuth",
            "password_change": "Password changed",
            "email_change": "Email changed",
            "profile_update": "Profile updated",
            "create": f"{self.entity_type} created",
            "update": f"{self.entity_type} updated",
            "delete": f"{self.entity_type} deleted",
            "upload": "File uploaded",
        }
        return descriptions.get(self.action, self.action)
