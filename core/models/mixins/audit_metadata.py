"""
Audit Metadata Mixin.

Stores additional audit metadata like IP addresses and user agents.

Single Responsibility: Tracks request context for audit purposes.
"""

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import declarative_mixin


@declarative_mixin
class AuditMetadataMixin:
    """
    Mixin for storing additional audit metadata.

    Tracks IP addresses, user agents, and other context for security auditing.

    User Story: #53 - API Request/Response Logging (P2)

    Fields:
        created_by_ip: IP address that created the record
        created_by_user_agent: User agent that created the record
        updated_by_ip: IP address that last updated the record
        updated_by_user_agent: User agent that last updated the record

    Example:
        class SensitiveDocument(AuditMetadataMixin, BaseModel):
            title = Column(String)

        # In mutation/service
        doc = SensitiveDocument(
            title="Secret",
            created_by_ip=request.client.host,
            created_by_user_agent=request.headers.get('User-Agent')
        )

    Note:
        Set these fields manually when creating/updating records.
        Consider using middleware or service layer to automate this.
    """

    # Creation metadata
    created_by_ip = Column(
        String(45),  # IPv6 max length
        nullable=True,
        comment="IP address that created this record"
    )

    created_by_user_agent = Column(
        Text,
        nullable=True,
        comment="User agent that created this record"
    )

    # Last update metadata
    updated_by_ip = Column(
        String(45),
        nullable=True,
        comment="IP address that last updated this record"
    )

    updated_by_user_agent = Column(
        Text,
        nullable=True,
        comment="User agent that last updated this record"
    )
