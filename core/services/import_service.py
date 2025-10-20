"""
Import Service - импорт данных из различных форматов
"""

import json
import csv
import os
from typing import Any, Dict, List, Optional
from io import BytesIO

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import pandas as pd

from core.models.import_export_job import (
    ImportExportJobModel,
    JobStatus,
    JobType,
    EntityType,
)
from languages.models.concept import ConceptModel
from languages.models.dictionary import DictionaryModel
from languages.models.language import LanguageModel
from auth.models.user import UserModel
from auth.models.profile import UserProfileModel
from auth.services.auth_service import AuthService


class DuplicateStrategy(str):
    """Стратегии обработки дубликатов"""

    SKIP = "skip"
    UPDATE = "update"
    FAIL = "fail"


class ImportService:
    """Сервис для импорта данных"""

    def __init__(self, db: Session):
        self.db = db

    def create_import_job(
        self,
        user_id: int,
        entity_type: EntityType,
        file_url: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> ImportExportJobModel:
        """Создать задание импорта"""
        job = ImportExportJobModel(
            user_id=user_id,
            job_type=JobType.IMPORT,
            entity_type=entity_type,
            file_url=file_url,
            status=JobStatus.PENDING,
            options=options or {},
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def process_import(self, job_id: int, file_content: bytes) -> ImportExportJobModel:
        """Обработать импорт (синхронно)"""
        job = self.db.query(ImportExportJobModel).filter_by(id=job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        try:
            job.status = JobStatus.PROCESSING
            self.db.commit()

            # Парсим файл
            data = self._parse_file(file_content, job.file_url)
            job.total_count = len(data)
            self.db.commit()

            # Получаем опции
            on_duplicate = job.options.get("onDuplicate", DuplicateStrategy.SKIP)
            validate_only = job.options.get("validateOnly", False)

            errors = []
            processed_count = 0

            # Импортируем данные
            if job.entity_type == EntityType.CONCEPTS:
                processed_count, errors = self._import_concepts(
                    data, on_duplicate, validate_only
                )
            elif job.entity_type == EntityType.DICTIONARIES:
                processed_count, errors = self._import_dictionaries(
                    data, on_duplicate, validate_only
                )
            elif job.entity_type == EntityType.USERS:
                processed_count, errors = self._import_users(data, on_duplicate, validate_only)
            elif job.entity_type == EntityType.LANGUAGES:
                processed_count, errors = self._import_languages(
                    data, on_duplicate, validate_only
                )
            else:
                raise ValueError(f"Unknown entity type: {job.entity_type}")

            # Обновляем job
            job.processed_count = processed_count
            job.error_count = len(errors)
            job.errors = errors if errors else None
            job.status = JobStatus.COMPLETED if not errors else JobStatus.FAILED
            self.db.commit()
            self.db.refresh(job)

            return job

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            self.db.commit()
            raise

    def _parse_file(self, file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        """Парсинг файла (JSON, CSV, XLSX)"""
        if filename.endswith(".json"):
            return json.loads(file_content.decode("utf-8"))
        elif filename.endswith(".csv"):
            return self._parse_csv(file_content)
        elif filename.endswith(".xlsx"):
            return self._parse_xlsx(file_content)
        else:
            raise ValueError(f"Unsupported file format: {filename}")

    def _parse_csv(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Парсинг CSV"""
        df = pd.read_csv(BytesIO(file_content))
        return df.to_dict(orient="records")

    def _parse_xlsx(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Парсинг XLSX"""
        df = pd.read_excel(BytesIO(file_content))
        return df.to_dict(orient="records")

    def _import_concepts(
        self, data: List[Dict[str, Any]], on_duplicate: str, validate_only: bool
    ) -> tuple[int, List[Dict[str, Any]]]:
        """Импорт концепций"""
        errors = []
        processed_count = 0

        for idx, item in enumerate(data):
            try:
                # Валидация
                if "path" not in item:
                    errors.append({"row": idx + 1, "message": "Missing required field: path"})
                    continue

                if validate_only:
                    processed_count += 1
                    continue

                # Проверяем существование
                existing = (
                    self.db.query(ConceptModel).filter_by(path=item["path"]).first()
                    if "path" in item
                    else None
                )

                if existing:
                    if on_duplicate == DuplicateStrategy.SKIP:
                        continue
                    elif on_duplicate == DuplicateStrategy.UPDATE:
                        # Обновляем
                        if "parent_id" in item:
                            existing.parent_id = item["parent_id"]
                        if "depth" in item:
                            existing.depth = item["depth"]
                        processed_count += 1
                    elif on_duplicate == DuplicateStrategy.FAIL:
                        errors.append(
                            {"row": idx + 1, "message": f"Duplicate path: {item['path']}"}
                        )
                        continue
                else:
                    # Создаем новую концепцию
                    concept = ConceptModel(
                        parent_id=item.get("parent_id"),
                        path=item["path"],
                        depth=item.get("depth", 0),
                    )
                    self.db.add(concept)
                    processed_count += 1

                # Импортируем переводы (если есть)
                if "translations" in item and isinstance(item["translations"], list):
                    self._import_concept_translations(existing or concept, item["translations"])

            except Exception as e:
                errors.append({"row": idx + 1, "message": str(e)})

        if not validate_only:
            self.db.commit()

        return processed_count, errors

    def _import_concept_translations(
        self, concept: ConceptModel, translations: List[Dict[str, Any]]
    ):
        """Импорт переводов концепции"""
        for translation in translations:
            if "language_code" not in translation or "name" not in translation:
                continue

            # Найти язык
            language = (
                self.db.query(LanguageModel)
                .filter_by(code=translation["language_code"])
                .first()
            )
            if not language:
                continue

            # Проверить существование перевода
            existing_dict = (
                self.db.query(DictionaryModel)
                .filter_by(concept_id=concept.id, language_id=language.id)
                .first()
            )

            if existing_dict:
                # Обновляем
                existing_dict.name = translation["name"]
                existing_dict.description = translation.get("description")
                existing_dict.image = translation.get("image")
            else:
                # Создаем
                dictionary = DictionaryModel(
                    concept_id=concept.id,
                    language_id=language.id,
                    name=translation["name"],
                    description=translation.get("description"),
                    image=translation.get("image"),
                )
                self.db.add(dictionary)

    def _import_dictionaries(
        self, data: List[Dict[str, Any]], on_duplicate: str, validate_only: bool
    ) -> tuple[int, List[Dict[str, Any]]]:
        """Импорт словарей"""
        errors = []
        processed_count = 0

        for idx, item in enumerate(data):
            try:
                # Валидация
                required_fields = ["concept_id", "language_code", "name"]
                for field in required_fields:
                    if field not in item:
                        errors.append(
                            {"row": idx + 1, "message": f"Missing required field: {field}"}
                        )
                        continue

                if validate_only:
                    processed_count += 1
                    continue

                # Найти язык
                language = (
                    self.db.query(LanguageModel)
                    .filter_by(code=item["language_code"])
                    .first()
                )
                if not language:
                    errors.append(
                        {"row": idx + 1, "message": f"Language not found: {item['language_code']}"}
                    )
                    continue

                # Проверяем существование
                existing = (
                    self.db.query(DictionaryModel)
                    .filter_by(concept_id=item["concept_id"], language_id=language.id)
                    .first()
                )

                if existing:
                    if on_duplicate == DuplicateStrategy.SKIP:
                        continue
                    elif on_duplicate == DuplicateStrategy.UPDATE:
                        existing.name = item["name"]
                        existing.description = item.get("description")
                        existing.image = item.get("image")
                        processed_count += 1
                    elif on_duplicate == DuplicateStrategy.FAIL:
                        errors.append(
                            {
                                "row": idx + 1,
                                "message": f"Duplicate dictionary for concept {item['concept_id']}",
                            }
                        )
                        continue
                else:
                    dictionary = DictionaryModel(
                        concept_id=item["concept_id"],
                        language_id=language.id,
                        name=item["name"],
                        description=item.get("description"),
                        image=item.get("image"),
                    )
                    self.db.add(dictionary)
                    processed_count += 1

            except Exception as e:
                errors.append({"row": idx + 1, "message": str(e)})

        if not validate_only:
            self.db.commit()

        return processed_count, errors

    def _import_users(
        self, data: List[Dict[str, Any]], on_duplicate: str, validate_only: bool
    ) -> tuple[int, List[Dict[str, Any]]]:
        """Импорт пользователей"""
        errors = []
        processed_count = 0
        auth_service = AuthService(self.db)

        for idx, item in enumerate(data):
            try:
                # Валидация
                required_fields = ["username", "email"]
                for field in required_fields:
                    if field not in item:
                        errors.append(
                            {"row": idx + 1, "message": f"Missing required field: {field}"}
                        )
                        continue

                if validate_only:
                    processed_count += 1
                    continue

                # Проверяем существование (по email)
                existing = self.db.query(UserModel).filter_by(email=item["email"]).first()

                if existing:
                    if on_duplicate == DuplicateStrategy.SKIP:
                        continue
                    elif on_duplicate == DuplicateStrategy.UPDATE:
                        # Обновляем только безопасные поля
                        if "is_active" in item:
                            existing.is_active = item["is_active"]
                        if "is_verified" in item:
                            existing.is_verified = item["is_verified"]

                        # Обновляем профиль
                        if "profile" in item and existing.profile:
                            profile_data = item["profile"]
                            if "first_name" in profile_data:
                                existing.profile.first_name = profile_data["first_name"]
                            if "last_name" in profile_data:
                                existing.profile.last_name = profile_data["last_name"]
                            if "bio" in profile_data:
                                existing.profile.bio = profile_data["bio"]

                        processed_count += 1
                    elif on_duplicate == DuplicateStrategy.FAIL:
                        errors.append(
                            {"row": idx + 1, "message": f"Duplicate email: {item['email']}"}
                        )
                        continue
                else:
                    # Создаем нового пользователя
                    # НЕ импортируем пароли (требуется отдельная установка)
                    password = item.get("password", "ChangeMe123!")  # Временный пароль
                    password_hash = auth_service._hash_password(password)

                    user = UserModel(
                        username=item["username"],
                        email=item["email"],
                        password_hash=password_hash,
                        is_active=item.get("is_active", True),
                        is_verified=item.get("is_verified", False),
                    )
                    self.db.add(user)
                    self.db.flush()  # Чтобы получить user.id

                    # Создаем профиль
                    if "profile" in item:
                        profile_data = item["profile"]
                        profile = UserProfileModel(
                            user_id=user.id,
                            first_name=profile_data.get("first_name"),
                            last_name=profile_data.get("last_name"),
                            bio=profile_data.get("bio"),
                        )
                        self.db.add(profile)

                    processed_count += 1

            except Exception as e:
                errors.append({"row": idx + 1, "message": str(e)})

        if not validate_only:
            self.db.commit()

        return processed_count, errors

    def _import_languages(
        self, data: List[Dict[str, Any]], on_duplicate: str, validate_only: bool
    ) -> tuple[int, List[Dict[str, Any]]]:
        """Импорт языков"""
        errors = []
        processed_count = 0

        for idx, item in enumerate(data):
            try:
                # Валидация
                required_fields = ["code", "name"]
                for field in required_fields:
                    if field not in item:
                        errors.append(
                            {"row": idx + 1, "message": f"Missing required field: {field}"}
                        )
                        continue

                if validate_only:
                    processed_count += 1
                    continue

                # Проверяем существование
                existing = self.db.query(LanguageModel).filter_by(code=item["code"]).first()

                if existing:
                    if on_duplicate == DuplicateStrategy.SKIP:
                        continue
                    elif on_duplicate == DuplicateStrategy.UPDATE:
                        existing.name = item["name"]
                        existing.native_name = item.get("native_name")
                        existing.rtl = item.get("rtl", False)
                        processed_count += 1
                    elif on_duplicate == DuplicateStrategy.FAIL:
                        errors.append(
                            {"row": idx + 1, "message": f"Duplicate code: {item['code']}"}
                        )
                        continue
                else:
                    language = LanguageModel(
                        code=item["code"],
                        name=item["name"],
                        native_name=item.get("native_name"),
                        rtl=item.get("rtl", False),
                    )
                    self.db.add(language)
                    processed_count += 1

            except Exception as e:
                errors.append({"row": idx + 1, "message": str(e)})

        if not validate_only:
            self.db.commit()

        return processed_count, errors
