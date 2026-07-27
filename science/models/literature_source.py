from __future__ import annotations

import enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Index, Integer, JSON, String, Text

from core.models.base import BaseModel


class LiteratureSourceParseStatus(str, enum.Enum):
    raw = "raw"
    parsed = "parsed"
    reviewed = "reviewed"
    found = "found"
    not_found = "not_found"
    downloaded = "downloaded"


class LiteratureSourcePublicationType(str, enum.Enum):
    book = "book"
    article = "article"
    conference = "conference"
    thesis = "thesis"
    report = "report"
    review = "review"
    preprint = "preprint"
    patent = "patent"
    other = "other"


class LiteratureSourceSearchStatus(str, enum.Enum):
    pending = "pending"
    searched = "searched"
    found = "found"
    not_found = "not_found"
    ambiguous = "ambiguous"
    error = "error"


class LiteratureSourceModel(BaseModel):
    """Independent literature-source record for bibliography ingestion."""

    __tablename__ = "literature_sources"

    raw_citation = Column(Text, nullable=False, unique=True, comment="Original citation text")
    parse_status = Column(
        SQLEnum(LiteratureSourceParseStatus),
        nullable=False,
        default=LiteratureSourceParseStatus.parsed,
        index=True,
        comment="Parsing/review status",
    )

    authors_text = Column(Text, nullable=True, index=True, comment="Authors as a searchable string")
    authors = Column(JSON, nullable=True, comment="Parsed authors array")
    title = Column(Text, nullable=False, comment="Parsed title")
    publication_year = Column(Integer, nullable=True, index=True, comment="Parsed publication year")
    publication_type = Column(
        SQLEnum(LiteratureSourcePublicationType),
        nullable=True,
        index=True,
        comment="Parsed publication type",
    )

    journal_or_book_title = Column(String(500), nullable=True, index=True)
    publisher = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)
    volume = Column(String(100), nullable=True)
    issue = Column(String(100), nullable=True)
    pages = Column(String(100), nullable=True)
    doi = Column(String(255), nullable=True, index=True)
    isbn = Column(String(50), nullable=True, index=True)
    article_number = Column(String(100), nullable=True)

    read_url = Column(Text, nullable=True, comment="URL where the source can be read")
    download_url = Column(Text, nullable=True, comment="URL where the source file can be downloaded")
    disk_path = Column(Text, nullable=True, comment="Local path where the source file is stored")
    file_format = Column(String(50), nullable=True)
    file_checksum = Column(String(128), nullable=True, index=True)

    search_query = Column(Text, nullable=True)
    search_status = Column(
        SQLEnum(LiteratureSourceSearchStatus),
        nullable=True,
        default=LiteratureSourceSearchStatus.pending,
        index=True,
    )
    search_checked_at = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)
    source_metadata = Column(JSON, nullable=True, comment="Importer/search enrichment metadata")

    __table_args__ = (
        Index("ix_literature_sources_author_year", "authors_text", "publication_year"),
        Index("ix_literature_sources_title_year", "title", "publication_year"),
    )

    def __repr__(self) -> str:
        return f"<LiteratureSource(id={self.id}, year={self.publication_year}, title={self.title!r})>"
