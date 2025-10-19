from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.models.base import BaseModel
from core.database import Base

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


class UserRoleModel(Base):
    """Association table for many-to-many User-Role relationship with timestamps"""
    __tablename__ = "user_roles_association"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    user = relationship("UserModel", back_populates="roles")
    role = relationship("RoleModel")
