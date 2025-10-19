from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from core.models.base import BaseModel
from core.models.mixins.soft_delete import SoftDeleteMixin


class LanguageModel(SoftDeleteMixin, BaseModel):
    """Модель языка"""

    __tablename__ = "languages"

    code = Column(String(2), nullable=False, unique=True, index=True, comment="ISO 639-1 код языка")
    name = Column(String(50), nullable=False, comment="Название языка")

    # Связи
    dictionaries = relationship(
        "DictionaryModel", back_populates="language", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Language(id={self.id}, code={self.code}, name={self.name})>"
