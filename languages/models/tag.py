from sqlalchemy import Column, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import relationship

from core.models.base import BaseModel
from core.models.mixins.soft_delete import SoftDeleteMixin


class TagModel(SoftDeleteMixin, BaseModel):
    """Модель тега для категоризации концепций"""

    __tablename__ = "tags"

    name = Column(String(100), nullable=False, unique=True, index=True, comment="Название тега")
    color = Column(String(7), nullable=True, comment="Цвет тега в формате #RRGGBB (опционально)")

    # Связи
    concept_tags = relationship("ConceptTagModel", back_populates="tag")

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>"


class ConceptTagModel(SoftDeleteMixin, BaseModel):
    """Назначение тега концепции.

    Полноценная сущность (не голая association-таблица): created_at/deleted_at
    хранят историю привязки/отвязки тега. Уникальность — частичный индекс
    только среди активных строк, повторная привязка после отвязки создаёт
    новую запись, сохраняя хронологию.
    """

    __tablename__ = "concept_tags"

    concept_id = Column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)

    # Связи
    concept = relationship("ConceptModel", back_populates="concept_tags")
    tag = relationship("TagModel", back_populates="concept_tags")

    __table_args__ = (
        Index(
            "uq_concept_tags_active_concept_tag",
            "concept_id",
            "tag_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    def __repr__(self):
        return f"<ConceptTag(concept_id={self.concept_id}, tag_id={self.tag_id})>"
