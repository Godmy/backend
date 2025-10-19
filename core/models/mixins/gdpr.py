"""
GDPR Compliance Mixin.

Provides fields and methods for GDPR compliance, specifically the "right to be forgotten".

Single Responsibility: Manages anonymization tracking.
"""

from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Session, declarative_mixin
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
from typing import Optional


@declarative_mixin
class GDPRMixin:
    """
    Mixin for GDPR compliance.

    Adds fields for tracking anonymization (right to be forgotten).

    User Story: #40 - GDPR Compliance Tools (P2)

    Fields:
        is_anonymized: Flag indicating if record is anonymized
        anonymized_at: Timestamp when anonymized
        anonymized_by_id: ID of user who performed anonymization
        anonymized_by: Relationship to User

    Methods:
        anonymize(): Mark record as anonymized

    Important:
        This mixin only sets anonymization flags. The actual anonymization
        of personal data should be done by the service layer.

    Example:
        class User(GDPRMixin, BaseModel):
            email = Column(String)
            first_name = Column(String)

        # In service layer
        def anonymize_user(db, user, admin_id):
            # Replace personal data
            user.email = f"deleted_{user.id}@local"
            user.first_name = "Deleted"

            # Set flag
            user.anonymize(db, anonymized_by_user_id=admin_id)
    """

    is_anonymized = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether this record has been anonymized (GDPR)"
    )

    anonymized_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when record was anonymized"
    )

    @declared_attr
    def anonymized_by_id(cls):
        """Foreign key to user who anonymized this record."""
        return Column(
            Integer,
            ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment="User ID who anonymized this record"
        )

    @declared_attr
    def anonymized_by(cls):
        """Relationship to user who anonymized this record."""
        return relationship(
            "User",
            foreign_keys=[cls.anonymized_by_id],
            uselist=False
        )

    # ========================================================================
    # ANONYMIZATION
    # ========================================================================

    def anonymize(self, db: Session, anonymized_by_user_id: Optional[int] = None) -> None:
        """
        Mark this record as anonymized.

        Note: This method only sets the flag. The actual anonymization
        of personal data should be done by the service layer before
        calling this method.

        Args:
            db: Database session
            anonymized_by_user_id: ID of user performing anonymization

        Example:
            # Service layer
            user.email = f"anonymized_{user.id}@deleted.local"
            user.first_name = "Deleted"
            user.last_name = "User"
            user.anonymize(db, anonymized_by_user_id=admin.id)
        """
        self.is_anonymized = True
        self.anonymized_at = datetime.utcnow()
        self.anonymized_by_id = anonymized_by_user_id
        db.commit()
