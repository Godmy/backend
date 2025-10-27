"""
Модель для хранения информации о загруженных файлах
"""

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, String
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
    mime_type = Column(String(127), nullable=False, index=True)  # MIME тип
    size = Column(BigInteger, nullable=False)  # Размер в байтах

    # Metadata
    file_type = Column(String(50), nullable=False, index=True)  # 'avatar', 'attachment', 'image'
    width = Column(Integer, nullable=True)  # Ширина (для изображений)
    height = Column(Integer, nullable=True)  # Высота (для изображений)

    # Thumbnails
    has_thumbnail = Column(Boolean, default=False)
    thumbnail_path = Column(String(512), nullable=True)

    # Владелец файла
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Связанная сущность (опционально)
    entity_type = Column(String(50), nullable=True, index=True)  # 'profile', 'concept', 'post'
    entity_id = Column(Integer, nullable=True, index=True)

    # Composite indexes for common file queries
    __table_args__ = (
        # Index for finding files by entity
        Index('ix_files_entity', 'entity_type', 'entity_id'),
        # Index for user's files listing
        Index('ix_files_user_created', 'uploaded_by', 'created_at'),
        # Index for file type filtering
        Index('ix_files_type_created', 'file_type', 'created_at'),
    )

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
