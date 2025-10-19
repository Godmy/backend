"""
Pre-configured mixin combinations.

Provides commonly used combinations of mixins for convenience.

Single Responsibility: Pre-configured combinations to reduce boilerplate.
"""

from core.models.base import BaseModel
from .soft_delete import SoftDeleteMixin
from .versioned import VersionedMixin
from .audit_metadata import AuditMetadataMixin
from .tenant import TenantMixin


class FullAuditModel(SoftDeleteMixin, VersionedMixin, AuditMetadataMixin, BaseModel):
    """
    Pre-configured base model with full audit capabilities.

    Combines:
        - SoftDeleteMixin: Soft delete with deleted_at, deleted_by
        - VersionedMixin: Version tracking and optimistic locking
        - AuditMetadataMixin: IP addresses and user agents
        - BaseModel: Standard id and timestamps

    Use for models requiring complete audit trail.

    Example:
        class Contract(FullAuditModel):
            __tablename__ = "contracts"
            contract_number = Column(String(50))
            amount = Column(Numeric(12, 2))

        # Has all features:
        contract.soft_delete(db, deleted_by_user_id=admin.id)
        contract.restore(db)
        print(f"Version: {contract.version}")
        print(f"Created from IP: {contract.created_by_ip}")
    """
    __abstract__ = True


class TenantAwareModel(TenantMixin, SoftDeleteMixin, BaseModel):
    """
    Pre-configured base model for multi-tenant applications.

    Combines:
        - TenantMixin: Tenant isolation with tenant_id
        - SoftDeleteMixin: Soft delete functionality
        - BaseModel: Standard id and timestamps

    Use for SaaS applications with multiple organizations.

    Example:
        class Project(TenantAwareModel):
            __tablename__ = "projects"
            name = Column(String(255))

        # Tenant-filtered queries
        projects = Project.by_tenant(db, tenant_id=123).all()

        # Soft delete
        project.soft_delete(db, deleted_by_user_id=user.id)
    """
    __abstract__ = True
