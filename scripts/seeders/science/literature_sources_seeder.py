from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from science.models import LiteratureSourceModel
from scripts.seeders.base import BaseSeeder, SeederMetadata, registry

logger = logging.getLogger(__name__)


def _packages_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_literature_sources() -> list[dict[str, Any]]:
    source_path = _packages_root() / "docs" / "chat" / "20260726" / "005-CODEX-SOURCE.md"
    content = source_path.read_text(encoding="utf-8")
    json_block = content.split("```json", 1)[1].rsplit("```", 1)[0]
    records = json.loads(json_block)

    return [
        {
            "raw_citation": record["raw_citation"],
            "parse_status": record.get("parse_status") or "parsed",
            "authors_text": record.get("authors_text"),
            "authors": record.get("authors"),
            "title": record["title"],
            "publication_year": record.get("publication_year"),
            "publication_type": record.get("publication_type"),
            "journal_or_book_title": record.get("journal_or_book_title"),
            "publisher": record.get("publisher"),
            "city": record.get("city"),
            "volume": record.get("volume"),
            "issue": record.get("issue"),
            "pages": record.get("pages"),
            "doi": record.get("doi"),
            "isbn": record.get("isbn"),
            "article_number": record.get("article_number"),
            "read_url": record.get("read_url"),
            "download_url": record.get("download_url"),
            "disk_path": record.get("disk_path"),
            "file_format": record.get("file_format"),
            "file_checksum": record.get("file_checksum"),
            "search_query": record.get("search_query"),
            "search_status": record.get("search_status") or "pending",
            "notes": record.get("notes"),
            "source_metadata": record.get("metadata") or {},
        }
        for record in records
    ]


@registry.register("literature_sources")
class LiteratureSourcesSeeder(BaseSeeder):
    """Seed independent literature-source bibliography records."""

    @property
    def metadata(self) -> SeederMetadata:
        return SeederMetadata(
            name="literature_sources",
            version="1.0.0",
            description="Seed neurophotonics and photobiomodulation literature sources",
            dependencies=[],
        )

    def should_run(self) -> bool:
        return self.db.query(LiteratureSourceModel).first() is None

    def seed(self) -> None:
        records = _load_literature_sources()
        created = self.batch_insert(LiteratureSourceModel, records, batch_size=100)
        self.db.commit()
        self.metadata.records_created = created
