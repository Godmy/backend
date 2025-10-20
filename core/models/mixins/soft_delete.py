"""
Soft Delete Mixin.

Provides soft delete functionality - records are marked as deleted instead of
being permanently removed from the database.

Single Responsibility: Manages soft deletion lifecycle.
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Session, declarative_mixin
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
from typing import Optional


@declarative_mixin
class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.

    Adds deleted_at and deleted_by fields. Records are marked as deleted
    instead of being permanently removed from the database.

    User Story: #6 - Soft Delete для всех моделей (P2)

    Fields:
        deleted_at: Timestamp when record was deleted (NULL = active)
        deleted_by_id: ID of user who deleted the record
        deleted_by: Relationship to User who deleted

    Methods:
        soft_delete(): Mark record as deleted
        restore(): Restore deleted record
        is_deleted(): Check if record is deleted
        active(): Query builder for active records
        deleted(): Query builder for deleted records
        with_deleted(): Query builder for all records

    Example:
        class User(SoftDeleteMixin, BaseModel):
            username = Column(String)

        # Soft delete
        user.soft_delete(db, deleted_by_user_id=admin.id)

        # Query only active
        active_users = User.active(db).all()

        # Restore
        user.restore(db)
    """

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Soft delete timestamp (NULL = not deleted)"
    )

    @declared_attr
    def deleted_by_id(cls):
        """Foreign key to user who deleted this record."""
        return Column(
            Integer,
            ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment="User ID who soft-deleted this record"
        )

    @declared_attr
    def deleted_by(cls):
        """Relationship to user who deleted this record."""
        return relationship(
            "UserModel",
            foreign_keys=[cls.deleted_by_id],
            uselist=False
        )

    # ========================================================================
    # INSTANCE METHODS
    # ========================================================================

    def soft_delete(self, db: Session, deleted_by_user_id: Optional[int] = None) -> None:
        """
        Mark this record as deleted.

        Args:
            db: Database session
            deleted_by_user_id: ID of user performing the deletion
        """
        self.deleted_at = datetime.utcnow()
        self.deleted_by_id = deleted_by_user_id
        db.commit()

    def restore(self, db: Session) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.deleted_by_id = None
        db.commit()

    def is_deleted(self) -> bool:
        """Check if this record is soft-deleted."""
        return self.deleted_at is not None

    # ========================================================================
    # CLASS METHODS (QUERY BUILDERS)
    # ========================================================================

    @classmethod
    def active(cls, db: Session):
        """Query builder for active (non-deleted) records."""
        return db.query(cls).filter(cls.deleted_at.is_(None))

    @classmethod
    def deleted(cls, db: Session):
        """Query builder for deleted records."""
        return db.query(cls).filter(cls.deleted_at.isnot(None))

    @classmethod
    def with_deleted(cls, db: Session):
        """Query builder for all records (including deleted)."""
        return db.query(cls)
