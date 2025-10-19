"""
Tenant Mixin.

Provides multi-tenancy support with row-level isolation.

Single Responsibility: Manages tenant relationship and filtering.
"""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, Session, declarative_mixin
from sqlalchemy.ext.declarative import declared_attr


@declarative_mixin
class TenantMixin:
    """
    Mixin for multi-tenancy support.

    Adds tenant_id for row-level isolation of data.
    All queries should be filtered by tenant to prevent data leakage.

    User Story: #29 - Multi-Tenancy Support (P3)

    Fields:
        tenant_id: ID of the organization/tenant
        tenant: Relationship to Organization

    Methods:
        by_tenant(): Query builder filtered by tenant

    Example:
        class User(TenantMixin, BaseModel):
            username = Column(String)

        # Query by tenant
        tenant_users = User.by_tenant(db, tenant_id=123).all()

    Security Note:
        Always use .by_tenant() or middleware to ensure tenant isolation.
        Never use raw db.query() as it bypasses tenant filtering.
    """

    @declared_attr
    def tenant_id(cls):
        """Foreign key to organization/tenant."""
        return Column(
            Integer,
            ForeignKey('organizations.id', ondelete='CASCADE'),
            nullable=False,
            index=True,  # Critical index for tenant filtering
            comment="Tenant/Organization ID for multi-tenancy"
        )

    @declared_attr
    def tenant(cls):
        """Relationship to organization/tenant."""
        return relationship(
            "Organization",
            foreign_keys=[cls.tenant_id],
            uselist=False
        )

    # ========================================================================
    # TENANT FILTERING
    # ========================================================================

    @classmethod
    def by_tenant(cls, db: Session, tenant_id: int):
        """
        Query builder for records belonging to a specific tenant.

        Args:
            db: Database session
            tenant_id: ID of the tenant

        Returns:
            Query object filtered by tenant

        Example:
            users = User.by_tenant(db, tenant_id=123).all()
            active_users = User.by_tenant(db, tenant_id=123).filter(
                User.is_active == True
            ).all()
        """
        return db.query(cls).filter(cls.tenant_id == tenant_id)
