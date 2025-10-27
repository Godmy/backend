from sqlalchemy import Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from core.models.base import BaseModel
from core.models.mixins.soft_delete import SoftDeleteMixin


class DictionaryModel(SoftDeleteMixin, BaseModel):
    """Модель словаря - связь концепции с языком"""

    __tablename__ = "dictionaries"

    concept_id = Column(
        Integer,
        ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID концепции",
    )
    language_id = Column(
        Integer,
        ForeignKey("languages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID языка",
    )
    name = Column(String(255), nullable=False, index=True, comment="Название на данном языке")
    description = Column(Text, comment="Описание")
    image = Column(String(255), comment="Путь к изображению")

    # Composite indexes for common dictionary queries
    __table_args__ = (
        # Unique constraint and index for concept-language pair
        Index('ix_dictionaries_concept_language', 'concept_id', 'language_id', unique=True),
        # Index for soft delete queries (name index already defined in Column)
        Index('ix_dictionaries_deleted', 'deleted_at'),
    )

    # Связи
    concept = relationship("ConceptModel", back_populates="dictionaries")
    language = relationship("LanguageModel", back_populates="dictionaries")

    def __repr__(self):
        return f"<Dictionary(id={self.id}, concept_id={self.concept_id}, language_id={self.language_id}, name={self.name})>"
