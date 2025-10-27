from sqlalchemy import Boolean, Column, Integer, String, Index
from sqlalchemy.orm import relationship

from core.models.base import BaseModel
from core.models.mixins.soft_delete import SoftDeleteMixin


class UserModel(SoftDeleteMixin, BaseModel):
    __tablename__ = "users"

    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)  # Added index for admin queries
    is_verified = Column(Boolean, default=False, index=True)  # Added index for filtering

    # Composite indexes for common query patterns
    __table_args__ = (
        # Index for active and verified user queries (admin panel)
        Index('ix_users_active_verified', 'is_active', 'is_verified'),
        # Index for soft delete with activity status
        Index('ix_users_deleted_active', 'deleted_at', 'is_active'),
    )

    # Связи
    roles = relationship("UserRoleModel", back_populates="user")
    profile = relationship("UserProfileModel", back_populates="user", uselist=False)
    oauth_connections = relationship("OAuthConnectionModel", back_populates="user")
