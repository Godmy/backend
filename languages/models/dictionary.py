from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from core.models.base import BaseModel


class DictionaryModel(BaseModel):
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
    name = Column(String(255), nullable=False, comment="Название на данном языке")
    description = Column(Text, comment="Описание")
    image = Column(String(255), comment="Путь к изображению")

    # Связи
    concept = relationship("ConceptModel", back_populates="dictionaries")
    language = relationship("LanguageModel", back_populates="dictionaries")

    def __repr__(self):
        return f"<Dictionary(id={self.id}, concept_id={self.concept_id}, language_id={self.language_id}, name={self.name})>"
