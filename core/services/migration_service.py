"""
Data Migration Service - Selective export/import with transformation and rollback.

Provides comprehensive data migration functionality with:
- Selective export by entities, dates, and filters
- Data transformation during migration
- Dry-run mode for verification
- Rollback mechanism
- Progress reporting

Implementation for User Story #34 - Data Migration Tools

Features:
    - Export specific entities with filters
    - Date range filtering
    - Data transformation (field mapping, anonymization)
    - Dry-run mode
    - Rollback snapshots
    - Progress reporting for large datasets
    - Multiple formats (JSON, CSV, SQL)

Usage:
    from core.services.migration_service import MigrationService

    # Export users created in last 30 days
    migration = MigrationService(db)
    migration.export_data(
        entities=["users"],
        filters={"created_after": "2024-01-01"},
        output_format="json",
        output_path="users_export.json"
    )

    # Import with transformation
    migration.import_data(
        input_path="users_export.json",
        transform_fn=anonymize_emails,
        dry_run=True
    )
"""

import csv
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import inspect, and_, or_

from core.structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class MigrationSnapshot:
    """Snapshot for rollback functionality."""
    snapshot_id: str
    created_at: datetime
    entities: List[str]
    record_count: int
    data_path: str


class MigrationService:
    """Service for data migration operations."""

    def __init__(self, db: Session, snapshot_dir: Optional[str] = None):
        """
        Initialize MigrationService.

        Args:
            db: Database session
            snapshot_dir: Directory for rollback snapshots (default: migrations/snapshots/)
        """
        self.db = db
        self.snapshot_dir = Path(snapshot_dir or "migrations/snapshots")
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def export_data(
        self,
        entities: List[str],
        output_path: str,
        output_format: str = "json",
        filters: Optional[Dict[str, Any]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        transform_fn: Optional[Callable[[Dict], Dict]] = None,
        dry_run: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Export data selectively.

        Args:
            entities: List of entity names to export (e.g., ["users", "concepts"])
            output_path: Output file path
            output_format: Output format (json, csv, sql)
            filters: Additional filters (e.g., {"is_active": True})
            date_range: Date range filter (start_date, end_date)
            transform_fn: Optional transformation function
            dry_run: Don't write file, just report what would be exported
            progress_callback: Callback for progress reporting (current, total)

        Returns:
            Export statistics dictionary

        Raises:
            ValueError: If invalid entity or format
        """
        logger.info(f"Exporting data: entities={entities}, format={output_format}, dry_run={dry_run}")

        if output_format not in ["json", "csv", "sql"]:
            raise ValueError(f"Unsupported output format: {output_format}")

        stats = {
            "entities": {},
            "total_records": 0,
            "dry_run": dry_run,
            "output_path": output_path if not dry_run else None
        }

        exported_data = {}

        for entity_name in entities:
            logger.info(f"Exporting entity: {entity_name}")

            # Get model class
            model_class = self._get_model_class(entity_name)
            if not model_class:
                logger.warning(f"Unknown entity: {entity_name}, skipping")
                continue

            # Build query
            query = self.db.query(model_class)

            # Apply date range filter
            if date_range:
                start_date, end_date = date_range
                if hasattr(model_class, "created_at"):
                    query = query.filter(
                        and_(
                            model_class.created_at >= start_date,
                            model_class.created_at <= end_date
                        )
                    )

            # Apply custom filters
            if filters:
                for field, value in filters.items():
                    if hasattr(model_class, field):
                        query = query.filter(getattr(model_class, field) == value)

            # Get total count
            total = query.count()
            stats["entities"][entity_name] = {"count": total}
            stats["total_records"] += total

            if dry_run:
                logger.info(f"Would export {total} {entity_name} records")
                continue

            # Export records
            records = []
            for i, record in enumerate(query.all()):
                # Convert to dict
                record_dict = self._model_to_dict(record)

                # Apply transformation
                if transform_fn:
                    record_dict = transform_fn(record_dict)

                records.append(record_dict)

                # Progress callback
                if progress_callback and (i + 1) % 100 == 0:
                    progress_callback(i + 1, total)

            exported_data[entity_name] = records
            logger.info(f"Exported {len(records)} {entity_name} records")

        # Write output file
        if not dry_run:
            if output_format == "json":
                self._write_json(output_path, exported_data)
            elif output_format == "csv":
                self._write_csv(output_path, exported_data)
            elif output_format == "sql":
                self._write_sql(output_path, exported_data)

            logger.info(f"Export completed: {output_path}")

        return stats

    def import_data(
        self,
        input_path: str,
        input_format: str = "json",
        entities: Optional[List[str]] = None,
        transform_fn: Optional[Callable[[Dict], Dict]] = None,
        dry_run: bool = False,
        create_snapshot: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Import data with optional transformation.

        Args:
            input_path: Input file path
            input_format: Input format (json, csv, sql)
            entities: List of entities to import (None = all)
            transform_fn: Optional transformation function
            dry_run: Don't actually import, just validate
            create_snapshot: Create rollback snapshot before import
            progress_callback: Callback for progress reporting

        Returns:
            Import statistics dictionary

        Raises:
            ValueError: If invalid format or data
        """
        logger.info(f"Importing data: path={input_path}, format={input_format}, dry_run={dry_run}")

        if input_format not in ["json", "csv", "sql"]:
            raise ValueError(f"Unsupported input format: {input_format}")

        # Create snapshot for rollback
        snapshot = None
        if create_snapshot and not dry_run:
            snapshot = self.create_snapshot(entities or [])

        stats = {
            "entities": {},
            "total_records": 0,
            "dry_run": dry_run,
            "snapshot_id": snapshot.snapshot_id if snapshot else None
        }

        try:
            # Read input file
            if input_format == "json":
                imported_data = self._read_json(input_path)
            elif input_format == "csv":
                imported_data = self._read_csv(input_path)
            elif input_format == "sql":
                # SQL import uses psql directly
                return self._import_sql(input_path, dry_run)

            # Import each entity
            for entity_name, records in imported_data.items():
                if entities and entity_name not in entities:
                    logger.info(f"Skipping entity: {entity_name}")
                    continue

                logger.info(f"Importing entity: {entity_name}")

                model_class = self._get_model_class(entity_name)
                if not model_class:
                    logger.warning(f"Unknown entity: {entity_name}, skipping")
                    continue

                imported_count = 0
                for i, record_dict in enumerate(records):
                    # Apply transformation
                    if transform_fn:
                        record_dict = transform_fn(record_dict)

                    if not dry_run:
                        # Create model instance
                        instance = model_class(**record_dict)
                        self.db.add(instance)
                        imported_count += 1

                    # Progress callback
                    if progress_callback and (i + 1) % 100 == 0:
                        progress_callback(i + 1, len(records))

                if not dry_run:
                    self.db.commit()

                stats["entities"][entity_name] = {"count": imported_count}
                stats["total_records"] += imported_count
                logger.info(f"Imported {imported_count} {entity_name} records")

            return stats

        except Exception as e:
            logger.error(f"Import failed: {e}", exc_info=True)
            if not dry_run:
                self.db.rollback()

            # Rollback to snapshot if available
            if snapshot and not dry_run:
                logger.warning("Import failed, rolling back to snapshot")
                self.rollback_to_snapshot(snapshot.snapshot_id)

            raise

    def create_snapshot(self, entities: List[str]) -> MigrationSnapshot:
        """
        Create rollback snapshot.

        Args:
            entities: List of entities to snapshot

        Returns:
            MigrationSnapshot object
        """
        snapshot_id = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        snapshot_path = self.snapshot_dir / f"{snapshot_id}.json"

        logger.info(f"Creating snapshot: {snapshot_id}")

        # Export current data
        stats = self.export_data(
            entities=entities,
            output_path=str(snapshot_path),
            output_format="json",
            dry_run=False
        )

        snapshot = MigrationSnapshot(
            snapshot_id=snapshot_id,
            created_at=datetime.now(),
            entities=entities,
            record_count=stats["total_records"],
            data_path=str(snapshot_path)
        )

        # Save snapshot metadata
        metadata_path = self.snapshot_dir / f"{snapshot_id}.meta.json"
        with open(metadata_path, "w") as f:
            json.dump(asdict(snapshot), f, indent=2, default=str)

        logger.info(f"Snapshot created: {snapshot_id} ({snapshot.record_count} records)")
        return snapshot

    def rollback_to_snapshot(self, snapshot_id: str) -> bool:
        """
        Rollback to snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            True if rollback successful

        Raises:
            ValueError: If snapshot not found
        """
        logger.info(f"Rolling back to snapshot: {snapshot_id}")

        # Load snapshot metadata
        metadata_path = self.snapshot_dir / f"{snapshot_id}.meta.json"
        if not metadata_path.exists():
            raise ValueError(f"Snapshot not found: {snapshot_id}")

        with open(metadata_path, "r") as f:
            snapshot_data = json.load(f)
            snapshot = MigrationSnapshot(**snapshot_data)

        # Delete current data for entities
        for entity_name in snapshot.entities:
            model_class = self._get_model_class(entity_name)
            if model_class:
                self.db.query(model_class).delete()

        self.db.commit()

        # Import snapshot data
        self.import_data(
            input_path=snapshot.data_path,
            input_format="json",
            entities=snapshot.entities,
            dry_run=False,
            create_snapshot=False
        )

        logger.info(f"Rollback completed: {snapshot_id}")
        return True

    def list_snapshots(self) -> List[MigrationSnapshot]:
        """
        List all available snapshots.

        Returns:
            List of MigrationSnapshot objects
        """
        snapshots = []
        for metadata_file in self.snapshot_dir.glob("*.meta.json"):
            with open(metadata_file, "r") as f:
                data = json.load(f)
                if "created_at" in data and isinstance(data["created_at"], str):
                    data["created_at"] = datetime.fromisoformat(data["created_at"])
                snapshots.append(MigrationSnapshot(**data))

        snapshots.sort(key=lambda s: s.created_at, reverse=True)
        return snapshots

    # Private helper methods

    def _get_model_class(self, entity_name: str):
        """Get model class by entity name."""
        # Map entity names to model classes
        entity_map = {
            "users": "auth.models.user.UserModel",
            "roles": "auth.models.role.RoleModel",
            "concepts": "languages.models.concept.ConceptModel",
            "dictionaries": "languages.models.dictionary.DictionaryModel",
            "languages": "languages.models.language.LanguageModel",
            "files": "core.models.file.File",
            "audit_logs": "core.models.audit_log.AuditLog",
        }

        model_path = entity_map.get(entity_name)
        if not model_path:
            return None

        # Import model class dynamically
        try:
            module_path, class_name = model_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except Exception as e:
            logger.error(f"Failed to import model {model_path}: {e}")
            return None

    def _model_to_dict(self, instance) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        result = {}
        for column in inspect(instance).mapper.column_attrs:
            value = getattr(instance, column.key)
            # Convert datetime to string
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.key] = value
        return result

    def _write_json(self, path: str, data: Dict[str, List[Dict]]) -> None:
        """Write data to JSON file."""
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _read_json(self, path: str) -> Dict[str, List[Dict]]:
        """Read data from JSON file."""
        with open(path, "r") as f:
            return json.load(f)

    def _write_csv(self, path: str, data: Dict[str, List[Dict]]) -> None:
        """Write data to CSV file (one file per entity)."""
        base_path = Path(path).stem
        base_dir = Path(path).parent

        for entity_name, records in data.items():
            if not records:
                continue

            entity_path = base_dir / f"{base_path}_{entity_name}.csv"
            with open(entity_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)

    def _read_csv(self, path: str) -> Dict[str, List[Dict]]:
        """Read data from CSV files."""
        # TODO: Implement CSV reading
        raise NotImplementedError("CSV import not yet implemented")

    def _write_sql(self, path: str, data: Dict[str, List[Dict]]) -> None:
        """Write data as SQL INSERT statements."""
        # TODO: Implement SQL export
        raise NotImplementedError("SQL export not yet implemented")

    def _import_sql(self, path: str, dry_run: bool) -> Dict[str, Any]:
        """Import SQL file using psql."""
        # TODO: Implement SQL import
        raise NotImplementedError("SQL import not yet implemented")


# Transformation functions

def anonymize_emails(record: Dict[str, Any]) -> Dict[str, Any]:
    """Anonymize email addresses in record."""
    if "email" in record and record["email"]:
        username = record["email"].split("@")[0]
        record["email"] = f"{username}@example.com"
    return record


def anonymize_passwords(record: Dict[str, Any]) -> Dict[str, Any]:
    """Replace passwords with default hash."""
    if "hashed_password" in record:
        # bcrypt hash of "password123"
        record["hashed_password"] = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5EzEaVZQWKGxa"
    return record


def strip_pii(record: Dict[str, Any]) -> Dict[str, Any]:
    """Strip personally identifiable information."""
    pii_fields = ["email", "phone", "address", "ssn", "passport"]
    for field in pii_fields:
        if field in record:
            record[field] = None
    return record
