"""
OAuth Connection Model

Stores OAuth provider connections for users
"""

from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from core.models.base import BaseModel


class OAuthConnectionModel(BaseModel):
    """OAuth provider connection"""

    __tablename__ = "oauth_connections"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider = Column(
        String(50), nullable=False, index=True
    )  # 'google', 'telegram', 'github', etc.
    provider_user_id = Column(String(255), nullable=False, index=True)  # ID from provider
    provider_username = Column(String(255))  # Username from provider
    provider_email = Column(String(255))  # Email from provider
    access_token = Column(String(500))  # Optional: store access token
    refresh_token = Column(String(500))  # Optional: store refresh token
    extra_data = Column(JSON)  # Additional data from provider

    # Relationships
    user = relationship("UserModel", back_populates="oauth_connections")

    def __repr__(self):
        return f"<OAuthConnection(user_id={self.user_id}, provider={self.provider}, provider_user_id={self.provider_user_id})>"

    class Config:
        """Pydantic config"""

        from_attributes = True
