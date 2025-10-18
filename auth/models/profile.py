from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from core.models.base import BaseModel  # Изменяем импорт


class UserProfileModel(BaseModel):
    __tablename__ = "user_profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    bio = Column(String(500))
    avatar = Column(String(255))
    avatar_file_id = Column(Integer, ForeignKey("files.id"), nullable=True)  # Связь с файлом
    language = Column(String(5), default="en")
    timezone = Column(String(50), default="UTC")

    # Связи
    user = relationship("UserModel", back_populates="profile")
    avatar_file = relationship("File", foreign_keys=[avatar_file_id])


class OAuthConnectionModel(BaseModel):
    __tablename__ = "oauth_connections"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(20), nullable=False)
    provider_user_id = Column(String(100), nullable=False)
    access_token = Column(String(500))
    refresh_token = Column(String(500))

    # Связь
    user = relationship("UserModel", back_populates="oauth_connections")
