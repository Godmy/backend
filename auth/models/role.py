from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from core.models.base import BaseModel  # Изменяем импорт

# Связующая таблица для many-to-many пользователей и ролей
user_roles = Table(
    "user_roles",
    BaseModel.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE")),
)


class RoleModel(BaseModel):
    __tablename__ = "roles"

    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255))

    # Связи
    users = relationship("UserModel", secondary=user_roles, backref="role_users")
    permissions = relationship("PermissionModel", back_populates="role")


class UserRoleModel(BaseModel):
    __tablename__ = "user_roles_association"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)

    # Связи
    user = relationship("UserModel", back_populates="roles")
    role = relationship("RoleModel")
