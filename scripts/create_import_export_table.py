"""
Скрипт для создания таблицы import_export_jobs
"""

from core.database import engine
from core.models.import_export_job import ImportExportJobModel
from core.models.base import BaseModel

if __name__ == "__main__":
    print("Creating import_export_jobs table...")
    BaseModel.metadata.create_all(engine, tables=[ImportExportJobModel.__table__])
    print("✓ Table created successfully")
