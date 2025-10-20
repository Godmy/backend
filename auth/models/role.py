from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from core.models.base import BaseModel
from core.database import Base


class RoleModel(BaseModel):
    __tablename__ = "roles"

    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255))

    # Связи
    permissions = relationship("PermissionModel", back_populates="role")
    user_roles = relationship("UserRoleModel", back_populates="role")


class UserRoleModel(Base):
    """Association table for many-to-many User-Role relationship"""
    __tablename__ = "user_roles_association"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)

    # Связи
    user = relationship("UserModel", back_populates="roles")
    role = relationship("RoleModel")
