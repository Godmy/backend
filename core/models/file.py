"""
Модель для хранения информации о загруженных файлах
"""
from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, BigInteger
from sqlalchemy.orm import relationship
from core.models.base import BaseModel

if TYPE_CHECKING:
    from auth.models.user import User


class File(BaseModel):
    """Модель загруженного файла"""

    __tablename__ = "files"

    # Основная информация
    filename = Column(String(255), nullable=False)  # Оригинальное имя файла
    stored_filename = Column(String(255), nullable=False, unique=True)  # Имя в хранилище
    filepath = Column(String(512), nullable=False)  # Путь к файлу
    mime_type = Column(String(127), nullable=False)  # MIME тип
    size = Column(BigInteger, nullable=False)  # Размер в байтах

    # Metadata
    file_type = Column(String(50), nullable=False)  # 'avatar', 'attachment', 'image'
    width = Column(Integer, nullable=True)  # Ширина (для изображений)
    height = Column(Integer, nullable=True)  # Высота (для изображений)

    # Thumbnails
    has_thumbnail = Column(Boolean, default=False)
    thumbnail_path = Column(String(512), nullable=True)

    # Владелец файла
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Связанная сущность (опционально)
    entity_type = Column(String(50), nullable=True)  # 'profile', 'concept', 'post'
    entity_id = Column(Integer, nullable=True)

    # Relationships
    user = relationship("UserModel", backref="uploaded_files")

    def __repr__(self):
        return f"<File {self.filename} ({self.file_type})>"

    @property
    def url(self):
        """URL для доступа к файлу"""
        return f"/uploads/{self.stored_filename}"

    @property
    def thumbnail_url(self):
        """URL для доступа к thumbnail"""
        if self.has_thumbnail and self.thumbnail_path:
            return f"/uploads/thumbnails/{self.stored_filename}"
        return None

    @property
    def size_mb(self):
        """Размер файла в MB"""
        return round(self.size / (1024 * 1024), 2)
