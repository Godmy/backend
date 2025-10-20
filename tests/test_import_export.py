"""
Тесты для системы импорта/экспорта
"""

import json
import os
import tempfile
from io import BytesIO

import pytest
from sqlalchemy.orm import Session

from core.models.import_export_job import (
    ImportExportJobModel,
    JobStatus,
    JobType,
    ExportFormat,
    EntityType,
)
from core.services.export_service import ExportService
from core.services.import_service import ImportService, DuplicateStrategy
from languages.models.concept import ConceptModel
from languages.models.dictionary import DictionaryModel
from languages.models.language import LanguageModel
from auth.models.user import UserModel


class TestExportService:
    """Тесты для ExportService"""

    def test_create_export_job(self, db: Session, test_user: UserModel):
        """Тест создания задания экспорта"""
        export_service = ExportService(db)

        job = export_service.create_export_job(
            user_id=test_user.id,
            entity_type=EntityType.CONCEPTS,
            format=ExportFormat.JSON,
            filters={"language": "en"},
        )

        assert job.id is not None
        assert job.user_id == test_user.id
        assert job.job_type == JobType.EXPORT
        assert job.entity_type == EntityType.CONCEPTS
        assert job.format == ExportFormat.JSON
        assert job.status == JobStatus.PENDING
        assert job.filters == {"language": "en"}

    def test_export_concepts_to_json(self, db: Session, test_user: UserModel, test_language: LanguageModel):
        """Тест экспорта концепций в JSON"""
        export_service = ExportService(db)

        # Создаем тестовую концепцию
        concept = ConceptModel(path="/test", depth=0)
        db.add(concept)
        db.commit()

        # Создаем перевод
        dictionary = DictionaryModel(
            concept_id=concept.id,
            language_id=test_language.id,
            name="Test Concept",
            description="Test Description",
        )
        db.add(dictionary)
        db.commit()

        # Создаем и обрабатываем задание
        job = export_service.create_export_job(
            user_id=test_user.id,
            entity_type=EntityType.CONCEPTS,
            format=ExportFormat.JSON,
        )

        result_job = export_service.process_export(job.id)

        assert result_job.status == JobStatus.COMPLETED
        assert result_job.file_url is not None
        assert result_job.total_count > 0
        assert result_job.processed_count == result_job.total_count

        # Проверяем что файл создан
        file_path = export_service.get_export_file_path(result_job.id)
        assert file_path is not None
        assert os.path.exists(file_path)

        # Проверяем содержимое
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) > 0

        # Cleanup
        os.remove(file_path)

    def test_export_languages_to_csv(self, db: Session, test_user: UserModel, test_language: LanguageModel):
        """Тест экспорта языков в CSV"""
        export_service = ExportService(db)

        job = export_service.create_export_job(
            user_id=test_user.id,
            entity_type=EntityType.LANGUAGES,
            format=ExportFormat.CSV,
        )

        result_job = export_service.process_export(job.id)

        assert result_job.status == JobStatus.COMPLETED
        assert result_job.file_url.endswith(".csv")

        # Cleanup
        file_path = export_service.get_export_file_path(result_job.id)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    def test_export_to_xlsx(self, db: Session, test_user: UserModel, test_language: LanguageModel):
        """Тест экспорта в XLSX"""
        export_service = ExportService(db)

        job = export_service.create_export_job(
            user_id=test_user.id,
            entity_type=EntityType.LANGUAGES,
            format=ExportFormat.XLSX,
        )

        result_job = export_service.process_export(job.id)

        assert result_job.status == JobStatus.COMPLETED
        assert result_job.file_url.endswith(".xlsx")

        # Cleanup
        file_path = export_service.get_export_file_path(result_job.id)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    def test_cleanup_old_exports(self, db: Session, test_user: UserModel):
        """Тест очистки старых экспортов"""
        export_service = ExportService(db)

        # Создаем тестовый файл
        test_file = os.path.join(export_service.export_dir, "test_old_file.json")
        with open(test_file, "w") as f:
            f.write("{}")

        # Очищаем файлы старше 0 часов (удалит все)
        deleted = export_service.cleanup_old_exports(hours=0)

        assert not os.path.exists(test_file)


class TestImportService:
    """Тесты для ImportService"""

    def test_create_import_job(self, db: Session, test_user: UserModel):
        """Тест создания задания импорта"""
        import_service = ImportService(db)

        job = import_service.create_import_job(
            user_id=test_user.id,
            entity_type=EntityType.CONCEPTS,
            file_url="test.json",
            options={"onDuplicate": "skip"},
        )

        assert job.id is not None
        assert job.user_id == test_user.id
        assert job.job_type == JobType.IMPORT
        assert job.entity_type == EntityType.CONCEPTS
        assert job.status == JobStatus.PENDING

    def test_import_languages_from_json(self, db: Session, test_user: UserModel):
        """Тест импорта языков из JSON"""
        import_service = ImportService(db)

        # Подготавливаем данные
        data = [
            {"code": "fr", "name": "French", "native_name": "Français", "rtl": False},
            {"code": "de", "name": "German", "native_name": "Deutsch", "rtl": False},
        ]

        file_content = json.dumps(data).encode("utf-8")

        job = import_service.create_import_job(
            user_id=test_user.id,
            entity_type=EntityType.LANGUAGES,
            file_url="languages.json",
        )

        result_job = import_service.process_import(job.id, file_content)

        assert result_job.status == JobStatus.COMPLETED
        assert result_job.processed_count == 2
        assert result_job.error_count == 0

        # Проверяем что языки созданы
        fr_lang = db.query(LanguageModel).filter_by(code="fr").first()
        assert fr_lang is not None
        assert fr_lang.name == "French"

    def test_import_concepts_with_translations(self, db: Session, test_user: UserModel, test_language: LanguageModel):
        """Тест импорта концепций с переводами"""
        import_service = ImportService(db)

        data = [
            {
                "path": "/imported/concept1",
                "depth": 1,
                "translations": [
                    {
                        "language_code": test_language.code,
                        "name": "Imported Concept 1",
                        "description": "Test import",
                    }
                ],
            }
        ]

        file_content = json.dumps(data).encode("utf-8")

        job = import_service.create_import_job(
            user_id=test_user.id,
            entity_type=EntityType.CONCEPTS,
            file_url="concepts.json",
        )

        result_job = import_service.process_import(job.id, file_content)

        assert result_job.status == JobStatus.COMPLETED
        assert result_job.processed_count == 1

        # Проверяем что концепция создана
        concept = db.query(ConceptModel).filter_by(path="/imported/concept1").first()
        assert concept is not None
        assert len(concept.dictionaries) > 0

    def test_import_duplicate_skip(self, db: Session, test_user: UserModel, test_language: LanguageModel):
        """Тест импорта с пропуском дубликатов"""
        import_service = ImportService(db)

        # Создаем существующий язык
        existing_lang = LanguageModel(code="es", name="Spanish", native_name="Español")
        db.add(existing_lang)
        db.commit()

        data = [
            {"code": "es", "name": "Spanish Updated", "native_name": "Español"},
            {"code": "it", "name": "Italian", "native_name": "Italiano"},
        ]

        file_content = json.dumps(data).encode("utf-8")

        job = import_service.create_import_job(
            user_id=test_user.id,
            entity_type=EntityType.LANGUAGES,
            file_url="languages.json",
            options={"onDuplicate": DuplicateStrategy.SKIP},
        )

        result_job = import_service.process_import(job.id, file_content)

        # Должен обработать только новый (it)
        assert result_job.processed_count == 1

        # Проверяем что существующий не обновился
        es_lang = db.query(LanguageModel).filter_by(code="es").first()
        assert es_lang.name == "Spanish"  # Не изменилось

    def test_import_duplicate_update(self, db: Session, test_user: UserModel):
        """Тест импорта с обновлением дубликатов"""
        import_service = ImportService(db)

        # Создаем существующий язык
        existing_lang = LanguageModel(code="pt", name="Portuguese", native_name="Português")
        db.add(existing_lang)
        db.commit()

        data = [{"code": "pt", "name": "Portuguese Updated", "native_name": "Português"}]

        file_content = json.dumps(data).encode("utf-8")

        job = import_service.create_import_job(
            user_id=test_user.id,
            entity_type=EntityType.LANGUAGES,
            file_url="languages.json",
            options={"onDuplicate": DuplicateStrategy.UPDATE},
        )

        result_job = import_service.process_import(job.id, file_content)

        assert result_job.processed_count == 1

        # Проверяем что обновилось
        pt_lang = db.query(LanguageModel).filter_by(code="pt").first()
        assert pt_lang.name == "Portuguese Updated"

    def test_import_validate_only(self, db: Session, test_user: UserModel):
        """Тест режима валидации без сохранения"""
        import_service = ImportService(db)

        data = [{"code": "ja", "name": "Japanese", "native_name": "日本語"}]

        file_content = json.dumps(data).encode("utf-8")

        initial_count = db.query(LanguageModel).count()

        job = import_service.create_import_job(
            user_id=test_user.id,
            entity_type=EntityType.LANGUAGES,
            file_url="languages.json",
            options={"validateOnly": True},
        )

        result_job = import_service.process_import(job.id, file_content)

        assert result_job.processed_count == 1

        # Проверяем что данные НЕ сохранились
        final_count = db.query(LanguageModel).count()
        assert final_count == initial_count

    def test_import_with_errors(self, db: Session, test_user: UserModel):
        """Тест импорта с ошибками валидации"""
        import_service = ImportService(db)

        # Данные с ошибкой (нет обязательного поля 'name')
        data = [{"code": "zh"}, {"code": "ko", "name": "Korean"}]

        file_content = json.dumps(data).encode("utf-8")

        job = import_service.create_import_job(
            user_id=test_user.id,
            entity_type=EntityType.LANGUAGES,
            file_url="languages.json",
        )

        result_job = import_service.process_import(job.id, file_content)

        # Должна быть минимум 1 ошибка
        assert result_job.error_count > 0
        assert result_job.errors is not None


# Fixtures
@pytest.fixture
def test_user(db: Session) -> UserModel:
    """Создать тестового пользователя"""
    from auth.services.auth_service import AuthService

    auth_service = AuthService(db)
    user = UserModel(
        username="test_export_user",
        email="export@test.com",
        password_hash=auth_service._hash_password("Test123!"),
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_language(db: Session) -> LanguageModel:
    """Создать тестовый язык"""
    lang = db.query(LanguageModel).filter_by(code="en").first()
    if not lang:
        lang = LanguageModel(code="en", name="English", native_name="English")
        db.add(lang)
        db.commit()
        db.refresh(lang)
    return lang
