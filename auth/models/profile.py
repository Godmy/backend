from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from core.models.base import BaseModel


class UserProfileModel(BaseModel):
    """User profile with additional information"""
    __tablename__ = "user_profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    bio = Column(String(500))
    avatar = Column(String(255))
    avatar_file_id = Column(Integer, ForeignKey("files.id"), nullable=True)  # Связь с файлом
    language = Column(String(5), default='en')
    timezone = Column(String(50), default='UTC')

    # Связи
    user = relationship("UserModel", back_populates="profile")
    avatar_file = relationship("File", foreign_keys=[avatar_file_id])