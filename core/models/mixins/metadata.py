"""
Generic Metadata Mixin.

Provides a JSON column for flexible metadata storage.

Single Responsibility: Manages arbitrary JSON metadata.
"""

from sqlalchemy import Column, JSON
from sqlalchemy.orm import declarative_mixin


@declarative_mixin
class MetadataMixin:
    """
    Mixin for storing arbitrary metadata.

    Adds a JSON column for flexible data storage without schema changes.
    Useful for user preferences, feature flags, or dynamic configurations.

    Fields:
        metadata: JSON column for arbitrary data

    Example:
        class User(MetadataMixin, BaseModel):
            username = Column(String)

        # Store preferences
        user.metadata = {
            "preferences": {"theme": "dark", "language": "ru"},
            "onboarding_completed": True
        }

        # Update nested values
        from sqlalchemy.orm.attributes import flag_modified

        user.metadata['preferences']['theme'] = 'light'
        flag_modified(user, 'metadata')  # Important!
        db.commit()

    Important:
        When updating nested values, you must call flag_modified()
        to notify SQLAlchemy of the change.
    """

    metadata = Column(
        JSON,
        nullable=True,
        default=dict,
        comment="Arbitrary JSON metadata for flexible data storage"
    )
