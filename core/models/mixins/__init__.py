"""
Database model mixins.

This package provides optional mixins for extending model functionality.
Each mixin follows the Single Responsibility Principle.

Available mixins:
    - SoftDeleteMixin: Soft delete functionality
    - VersionedMixin: Version tracking and optimistic locking
    - TenantMixin: Multi-tenancy support
    - GDPRMixin: GDPR compliance (anonymization)
    - AuditMetadataMixin: IP/User-Agent tracking
    - MetadataMixin: Generic JSON metadata storage

Pre-configured combinations:
    - FullAuditModel: Soft delete + versioning + audit metadata
    - TenantAwareModel: Tenant isolation + soft delete

Usage:
    from core.models.base import BaseModel
    from core.models.mixins import SoftDeleteMixin

    class User(SoftDeleteMixin, BaseModel):
        __tablename__ = "users"
        username = Column(String(100))
"""

from .soft_delete import SoftDeleteMixin
from .versioned import VersionedMixin
from .tenant import TenantMixin
from .gdpr import GDPRMixin
from .audit_metadata import AuditMetadataMixin
from .metadata import MetadataMixin
from .combinations import FullAuditModel, TenantAwareModel

__all__ = [
    # Individual mixins
    'SoftDeleteMixin',
    'VersionedMixin',
    'TenantMixin',
    'GDPRMixin',
    'AuditMetadataMixin',
    'MetadataMixin',

    # Pre-configured combinations
    'FullAuditModel',
    'TenantAwareModel',
]
