"""
Table Service - Universal service for working with database tables.

Provides functionality for introspecting database schema and performing
CRUD operations on any table dynamically.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import MetaData, Table, func, inspect, select, text
from sqlalchemy.engine import Inspector
from sqlalchemy.orm import Session

from core.platform.logging.structured_logging import get_logger

logger = get_logger(__name__)


class TableService:
    """Service for universal table operations."""

    BLACKLISTED_TABLES = {"alembic_version"}

    @staticmethod
    def get_all_tables(db: Session) -> List[Dict[str, Any]]:
        inspector: Inspector = inspect(db.bind)
        allowed_tables = [
            name
            for name in inspector.get_table_names()
            if name not in TableService.BLACKLISTED_TABLES
        ]
        result = []
        for table_name in sorted(allowed_tables):
            try:
                row_count = db.execute(
                    text(f'SELECT COUNT(*) FROM "{table_name}"')
                ).scalar()
                column_names = [col["name"] for col in inspector.get_columns(table_name)]
                result.append(
                    {
                        "name": table_name,
                        "row_count": row_count or 0,
                        "has_soft_delete": "deleted_at" in column_names,
                    }
                )
            except Exception as exc:
                logger.error("Error getting info for table %s: %s", table_name, exc)
                result.append(
                    {"name": table_name, "row_count": 0, "has_soft_delete": False}
                )
        logger.info("Retrieved %s tables from database", len(result))
        return result

    @staticmethod
    def get_table_schema(db: Session, table_name: str) -> Dict[str, Any]:
        TableService._validate_table_name(table_name)
        inspector: Inspector = inspect(db.bind)
        if table_name not in inspector.get_table_names():
            raise ValueError(f"Table '{table_name}' not found")
        primary_keys = inspector.get_pk_constraint(table_name).get(
            "constrained_columns", []
        )
        columns = [
            {
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col["nullable"],
                "primary_key": col["name"] in primary_keys,
                "default": str(col["default"]) if col["default"] is not None else None,
            }
            for col in inspector.get_columns(table_name)
        ]
        logger.info(
            "Retrieved schema for table '%s' with %s columns", table_name, len(columns)
        )
        return {"table_name": table_name, "columns": columns}

    @staticmethod
    def get_table_data(
        db: Session,
        table_name: str,
        limit: int = 50,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
    ) -> Dict[str, Any]:
        TableService._validate_table_name(table_name)
        if limit > 100:
            limit = 100
        inspector: Inspector = inspect(db.bind)
        if table_name not in inspector.get_table_names():
            raise ValueError(f"Table '{table_name}' not found")
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=db.bind)
        query = select(table)
        if filters:
            for column_name, value in filters.items():
                if hasattr(table.c, column_name):
                    query = query.where(table.c[column_name] == value)
        total = db.execute(select(func.count()).select_from(query.subquery())).scalar()
        if not order_by:
            primary_keys = inspector.get_pk_constraint(table_name).get(
                "constrained_columns", []
            )
            order_by = primary_keys[0] if primary_keys else "id"
        if hasattr(table.c, order_by):
            order_column = table.c[order_by]
            query = query.order_by(order_column.desc() if order_desc else order_column)
        result = db.execute(query.limit(limit).offset(offset))
        columns = list(result.keys())
        rows = []
        for row in result:
            item = {}
            for index, column_name in enumerate(columns):
                value = row[index]
                if isinstance(value, datetime):
                    value = value.isoformat()
                item[column_name] = value
            rows.append(item)
        logger.info(
            "Retrieved %s rows from table '%s' (offset=%s, limit=%s, total=%s)",
            len(rows),
            table_name,
            offset,
            limit,
            total,
        )
        return {
            "table_name": table_name,
            "columns": columns,
            "rows": rows,
            "total": total or 0,
            "has_more": (offset + len(rows)) < (total or 0),
        }

    @staticmethod
    def create_record(db: Session, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        TableService._validate_table_name(table_name)
        inspector: Inspector = inspect(db.bind)
        if table_name not in inspector.get_table_names():
            raise ValueError(f"Table '{table_name}' not found")
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=db.bind)
        valid_columns = {col.name for col in table.columns}
        invalid_columns = set(data.keys()) - valid_columns
        if invalid_columns:
            raise ValueError(f"Invalid columns: {invalid_columns}")
        result = db.execute(table.insert().values(**data))
        db.commit()
        primary_keys = inspector.get_pk_constraint(table_name).get(
            "constrained_columns", []
        )
        if primary_keys and result.inserted_primary_key:
            pk_column = primary_keys[0]
            pk_value = result.inserted_primary_key[0]
            created_row = db.execute(
                select(table).where(table.c[pk_column] == pk_value)
            ).first()
            if created_row:
                created_dict = dict(zip(created_row.keys(), created_row))
                for key, value in created_dict.items():
                    if isinstance(value, datetime):
                        created_dict[key] = value.isoformat()
                logger.info(
                    "Created record in table '%s' with ID %s", table_name, pk_value
                )
                return created_dict
        logger.info("Created record in table '%s'", table_name)
        return data

    @staticmethod
    def update_record(
        db: Session, table_name: str, record_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        TableService._validate_table_name(table_name)
        inspector: Inspector = inspect(db.bind)
        if table_name not in inspector.get_table_names():
            raise ValueError(f"Table '{table_name}' not found")
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=db.bind)
        primary_keys = inspector.get_pk_constraint(table_name).get(
            "constrained_columns", []
        )
        if not primary_keys:
            raise ValueError(f"Table '{table_name}' has no primary key")
        valid_columns = {col.name for col in table.columns}
        invalid_columns = set(data.keys()) - valid_columns
        if invalid_columns:
            raise ValueError(f"Invalid columns: {invalid_columns}")
        pk_column = primary_keys[0]
        result = db.execute(
            table.update().where(table.c[pk_column] == record_id).values(**data)
        )
        db.commit()
        if result.rowcount == 0:
            raise ValueError(
                f"Record with ID {record_id} not found in table '{table_name}'"
            )
        updated_row = db.execute(
            select(table).where(table.c[pk_column] == record_id)
        ).first()
        if updated_row:
            updated_dict = dict(zip(updated_row.keys(), updated_row))
            for key, value in updated_dict.items():
                if isinstance(value, datetime):
                    updated_dict[key] = value.isoformat()
            logger.info("Updated record %s in table '%s'", record_id, table_name)
            return updated_dict
        return data

    @staticmethod
    def delete_record(db: Session, table_name: str, record_id: int) -> bool:
        TableService._validate_table_name(table_name)
        inspector: Inspector = inspect(db.bind)
        if table_name not in inspector.get_table_names():
            raise ValueError(f"Table '{table_name}' not found")
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=db.bind)
        primary_keys = inspector.get_pk_constraint(table_name).get(
            "constrained_columns", []
        )
        if not primary_keys:
            raise ValueError(f"Table '{table_name}' has no primary key")
        pk_column = primary_keys[0]
        column_names = [col["name"] for col in inspector.get_columns(table_name)]
        if "deleted_at" in column_names:
            result = db.execute(
                table.update()
                .where(table.c[pk_column] == record_id)
                .values(deleted_at=datetime.utcnow())
            )
            db.commit()
            if result.rowcount == 0:
                raise ValueError(
                    f"Record with ID {record_id} not found in table '{table_name}'"
                )
            logger.info("Soft deleted record %s from table '%s'", record_id, table_name)
            return True
        result = db.execute(table.delete().where(table.c[pk_column] == record_id))
        db.commit()
        if result.rowcount == 0:
            raise ValueError(
                f"Record with ID {record_id} not found in table '{table_name}'"
            )
        logger.info("Hard deleted record %s from table '%s'", record_id, table_name)
        return True

    @staticmethod
    def _validate_table_name(table_name: str) -> None:
        if table_name in TableService.BLACKLISTED_TABLES:
            raise ValueError(f"Access to table '{table_name}' is not allowed")
