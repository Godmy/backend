from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from core.models.base import BaseModel
from core.models.mixins.soft_delete import SoftDeleteMixin

# Таблица связи многие-ко-многим для тегов и концепций
concept_tags = Table(
    'concept_tags',
    BaseModel.metadata,
    Column('concept_id', Integer, ForeignKey('concepts.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class TagModel(SoftDeleteMixin, BaseModel):
    """Модель тега для категоризации концепций"""

    __tablename__ = "tags"

    name = Column(String(100), nullable=False, unique=True, index=True, comment="Название тега")
    color = Column(String(7), nullable=True, comment="Цвет тега в формате #RRGGBB (опционально)")

    # Связи
    concepts = relationship(
        "ConceptModel",
        secondary=concept_tags,
        back_populates="tags"
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>"