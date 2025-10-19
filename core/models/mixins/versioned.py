"""
Versioned Mixin.

Provides version tracking and optimistic locking support.

Single Responsibility: Manages version tracking and change detection.
"""

from sqlalchemy import Column, Integer, String, event
from sqlalchemy.orm import declarative_mixin
import hashlib
import json
from typing import Dict, Any


@declarative_mixin
class VersionedMixin:
    """
    Mixin for optimistic locking and version tracking.

    Adds version number and content hash for tracking changes.
    Useful for version history and detecting concurrent modifications.

    User Story: #13 - Version History для концепций (P3)

    Fields:
        version: Version number (auto-increments on update)
        content_hash: SHA256 hash of record content

    Methods:
        increment_version(): Manually increment version
        calculate_hash(): Calculate content hash
        update_hash(): Update stored hash
        is_modified(): Check if content changed

    Auto-behavior:
        - Version increments automatically on update (via event listener)
        - Hash updates automatically on insert/update

    Example:
        class Concept(VersionedMixin, BaseModel):
            name = Column(String)

        # Auto-increments version on save
        concept.name = "New Name"
        concept.save(db)  # version: 1 → 2

        # Optimistic locking
        if concept.version != expected_version:
            raise ConflictError("Concurrent modification")
    """

    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Version number for optimistic locking"
    )

    content_hash = Column(
        String(64),
        nullable=True,
        comment="SHA256 hash of record content for change detection"
    )

    # ========================================================================
    # VERSION MANAGEMENT
    # ========================================================================

    def increment_version(self) -> None:
        """Increment the version number."""
        self.version = (self.version or 0) + 1

    # ========================================================================
    # HASH MANAGEMENT
    # ========================================================================

    def calculate_hash(self) -> str:
        """
        Calculate SHA256 hash of record content.

        Excludes: id, timestamps, version, hash itself.

        Returns:
            SHA256 hash as hex string
        """
        # Import here to avoid circular dependency
        try:
            data_dict = self.to_dict()
        except AttributeError:
            # Fallback if to_dict() not available
            data_dict = {c.name: getattr(self, c.name) for c in self.__table__.columns}

        excluded_fields = {'id', 'created_at', 'updated_at', 'version', 'content_hash'}

        data = {
            k: str(v) for k, v in data_dict.items()
            if k not in excluded_fields and v is not None
        }

        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def update_hash(self) -> None:
        """Update content hash."""
        self.content_hash = self.calculate_hash()

    def is_modified(self) -> bool:
        """
        Check if content has been modified since last hash update.

        Returns:
            True if content changed, False otherwise
        """
        current_hash = self.calculate_hash()
        return current_hash != self.content_hash


# ============================================================================
# EVENT LISTENERS
# ============================================================================

@event.listens_for(VersionedMixin, 'before_update', propagate=True)
def increment_version_on_update(mapper, connection, target):
    """
    Automatically increment version on update.

    This event listener is triggered before any update operation
    on models that inherit from VersionedMixin.
    """
    if hasattr(target, 'increment_version'):
        target.increment_version()
    if hasattr(target, 'update_hash'):
        target.update_hash()


@event.listens_for(VersionedMixin, 'before_insert', propagate=True)
def set_initial_hash(mapper, connection, target):
    """
    Set initial content hash on insert.
    """
    if hasattr(target, 'update_hash'):
        target.update_hash()
