from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from core.models.base import BaseModel
from core.models.mixins.soft_delete import SoftDeleteMixin


class UserModel(SoftDeleteMixin, BaseModel):
    __tablename__ = "users"

    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Связи
    roles = relationship("UserRoleModel", back_populates="user")
    profile = relationship("UserProfileModel", back_populates="user", uselist=False)
    oauth_connections = relationship("OAuthConnectionModel", back_populates="user")
