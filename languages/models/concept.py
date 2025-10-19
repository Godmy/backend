from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from core.models.base import BaseModel
from core.models.mixins.soft_delete import SoftDeleteMixin


class ConceptModel(SoftDeleteMixin, BaseModel):
    """Модель концепции (иерархическая структура)"""

    __tablename__ = "concepts"

    parent_id = Column(
        Integer,
        ForeignKey("concepts.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID родительской концепции",
    )
    path = Column(String(255), nullable=False, index=True, comment="Путь в дереве концепций")
    depth = Column(Integer, nullable=False, default=0, comment="Глубина вложенности")

    # Связи
    parent = relationship(
        "ConceptModel", remote_side="ConceptModel.id", backref="children", foreign_keys=[parent_id]
    )
    dictionaries = relationship(
        "DictionaryModel", back_populates="concept", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Concept(id={self.id}, path={self.path}, depth={self.depth})>"
