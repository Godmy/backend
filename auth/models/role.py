from sqlalchemy import Column, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import relationship

from core.models.base import BaseModel
from core.models.mixins.soft_delete import SoftDeleteMixin


class RoleModel(BaseModel):
    __tablename__ = "roles"

    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255))

    # Связи
    permissions = relationship("PermissionModel", back_populates="role")
    user_roles = relationship("UserRoleModel", back_populates="role")


class UserRoleModel(SoftDeleteMixin, BaseModel):
    """Назначение роли пользователю.

    Полноценная сущность (не голая association-таблица): created_at/deleted_at
    хранят историю выдачи и отзыва роли. Уникальность обеспечивается частичным
    индексом только среди активных строк, поэтому одну и ту же роль можно
    выдать повторно после отзыва — это создаёт новую запись, а не переиспользует
    старую, сохраняя полную хронологию.
    """

    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)

    # Связи
    user = relationship("UserModel", back_populates="roles", foreign_keys=[user_id])
    role = relationship("RoleModel", back_populates="user_roles")

    __table_args__ = (
        Index(
            "uq_user_roles_active_user_role",
            "user_id",
            "role_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
