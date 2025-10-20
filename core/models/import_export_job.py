from sqlalchemy import Column, ForeignKey, Integer, String, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from core.models.base import BaseModel


class JobStatus(str, enum.Enum):
    """Статусы задач импорта/экспорта"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, enum.Enum):
    """Типы задач"""

    EXPORT = "export"
    IMPORT = "import"


class ExportFormat(str, enum.Enum):
    """Форматы экспорта"""

    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"


class EntityType(str, enum.Enum):
    """Типы сущностей для экспорта/импорта"""

    CONCEPTS = "concepts"
    DICTIONARIES = "dictionaries"
    USERS = "users"
    LANGUAGES = "languages"


class ImportExportJobModel(BaseModel):
    """Модель задачи импорта/экспорта"""

    __tablename__ = "import_export_jobs"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_type = Column(SQLEnum(JobType), nullable=False, comment="Тип задачи (import/export)")
    entity_type = Column(SQLEnum(EntityType), nullable=False, comment="Тип сущности")
    status = Column(
        SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING, comment="Статус задачи"
    )

    # Для экспорта
    format = Column(SQLEnum(ExportFormat), nullable=True, comment="Формат экспорта")
    file_url = Column(String(500), nullable=True, comment="URL файла для скачивания/загрузки")
    expires_at = Column(Integer, nullable=True, comment="Timestamp истечения ссылки")

    # Прогресс
    total_count = Column(Integer, default=0, comment="Общее количество записей")
    processed_count = Column(Integer, default=0, comment="Обработано записей")
    error_count = Column(Integer, default=0, comment="Количество ошибок")

    # Ошибки и настройки
    errors = Column(JSON, nullable=True, comment="Список ошибок (для импорта)")
    filters = Column(JSON, nullable=True, comment="Фильтры для экспорта")
    options = Column(JSON, nullable=True, comment="Опции импорта (onDuplicate, validateOnly)")

    error_message = Column(Text, nullable=True, comment="Сообщение об ошибке")

    # Связи
    user = relationship("UserModel", backref="import_export_jobs")

    def __repr__(self):
        return f"<ImportExportJob(id={self.id}, type={self.job_type}, entity={self.entity_type}, status={self.status})>"

    @property
    def progress_percent(self) -> int:
        """Процент выполнения"""
        if self.total_count == 0:
            return 0
        return int((self.processed_count / self.total_count) * 100)