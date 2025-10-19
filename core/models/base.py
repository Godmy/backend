"""
Base model for all database models.

Provides core functionality: primary key, timestamps, and common query methods.
"""

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any

from core.database import Base


class BaseModel(Base):
    """
    Base model for all database models.

    Provides:
        - Auto-incrementing integer primary key
        - Created and updated timestamps (timezone-aware)
        - Common query methods

    Single Responsibility: Core model fields and basic CRUD operations.
    """
    __abstract__ = True

    # Primary key
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Primary key"
    )

    # Timestamps (timezone-aware)
    created_at = Column(
        DateTime(timezone=True),
        server_default='now()',
        nullable=False,
        index=True,
        comment="Record creation timestamp (UTC)"
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default='now()',
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Record last update timestamp (UTC)"
    )

    # ========================================================================
    # QUERY HELPERS
    # ========================================================================

    @classmethod
    def get_by_id(cls, db: Session, id: int) -> Optional['BaseModel']:
        """Get a record by ID."""
        return db.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_all(cls, db: Session, limit: int = 100, offset: int = 0):
        """Get all records with pagination."""
        return db.query(cls).limit(limit).offset(offset).all()

    @classmethod
    def count(cls, db: Session) -> int:
        """Count total records."""
        return db.query(cls).count()

    def save(self, db: Session) -> 'BaseModel':
        """Save the current instance."""
        db.add(self)
        db.commit()
        db.refresh(self)
        return self

    def delete(self, db: Session) -> None:
        """Delete the current instance (hard delete)."""
        db.delete(self)
        db.commit()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        Useful for serialization and logging.
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"
