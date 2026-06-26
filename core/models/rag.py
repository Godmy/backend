from __future__ import annotations

import enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, JSON, String, Text,
)
from sqlalchemy.orm import relationship

from core.models.base import BaseModel


class SourceType(str, enum.Enum):
    url = "url"
    file = "file"
    text = "text"
    git = "git"


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    indexing = "indexing"
    indexed = "indexed"
    error = "error"


class RagProject(BaseModel):
    __tablename__ = "rag_project"

    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    embedding_model = Column(String(255), nullable=False, default="nomic-embed-text")
    embedding_dim = Column(Integer, nullable=False, default=768)
    chunk_size = Column(Integer, nullable=False, default=512)
    chunk_overlap = Column(Integer, nullable=False, default=64)
    is_active = Column(Boolean, nullable=False, default=True)

    documents = relationship(
        "RagDocument", back_populates="project", cascade="all, delete-orphan"
    )


class RagDocument(BaseModel):
    __tablename__ = "rag_document"

    project_id = Column(
        Integer, ForeignKey("rag_project.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    source_type = Column(String(20), nullable=False)   # SourceType values
    source_uri = Column(Text, nullable=False)
    title = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default=DocumentStatus.pending, index=True)
    error_message = Column(Text, nullable=True)
    chunk_count = Column(Integer, nullable=False, default=0)
    indexed_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("RagProject", back_populates="documents")
    chunks = relationship(
        "RagChunk", back_populates="document", cascade="all, delete-orphan"
    )


class RagChunk(BaseModel):
    __tablename__ = "rag_chunk"

    document_id = Column(
        Integer, ForeignKey("rag_document.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    project_id = Column(
        Integer, ForeignKey("rag_project.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_metadata = Column(JSON, nullable=True)

    document = relationship("RagDocument", back_populates="chunks")
