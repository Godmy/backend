"""
Сидер для метаданных базы данных
Создаёт структуру таблиц и колонок БД как концепты
"""

import logging

from languages.models import ConceptModel, DictionaryModel, LanguageModel
from scripts.seeders.base import BaseSeeder, SeederMetadata, registry

logger = logging.getLogger(__name__)

# Метаданные БД (основные таблицы)
DB_METADATA = {
    "db/tables/users": {
        "en": "Users table",
        "ru": "Таблица пользователей",
    },
    "db/tables/users/columns/id": {
        "en": "User ID (primary key)",
        "ru": "ID пользователя (первичный ключ)",
    },
    "db/tables/users/columns/username": {
        "en": "Username (unique)",
        "ru": "Имя пользователя (уникальное)",
    },
    "db/tables/users/columns/email": {
        "en": "Email address",
        "ru": "Email адрес",
    },
    "db/tables/concepts": {
        "en": "Concepts table",
        "ru": "Таблица концептов",
    },
    "db/tables/concepts/columns/id": {
        "en": "Concept ID",
        "ru": "ID концепта",
    },
    "db/tables/concepts/columns/path": {
        "en": "Concept path",
        "ru": "Путь концепта",
    },
    "db/tables/concepts/columns/depth": {
        "en": "Depth in hierarchy",
        "ru": "Глубина в иерархии",
    },
    "db/tables/languages": {
        "en": "Languages table",
        "ru": "Таблица языков",
    },
    "db/tables/languages/columns/id": {
        "en": "Language ID",
        "ru": "ID языка",
    },
    "db/tables/languages/columns/code": {
        "en": "ISO language code",
        "ru": "ISO код языка",
    },
    "db/tables/languages/columns/name": {
        "en": "Language name",
        "ru": "Название языка",
    },
    "db/tables/dictionaries": {
        "en": "Dictionaries table (translations)",
        "ru": "Таблица словарей (переводы)",
    },
    "db/tables/roles": {
        "en": "Roles table",
        "ru": "Таблица ролей",
    },
    "db/tables/audit_logs": {
        "en": "Audit logs table",
        "ru": "Таблица логов аудита",
    },
}


@registry.register("db_concepts")
class DbConceptsSeeder(BaseSeeder):
    """Создание метаданных БД как концептов"""

    @property
    def metadata(self) -> SeederMetadata:
        return SeederMetadata(
            name="db_concepts",
            version="1.0.0",
            description=f"Создание метаданных БД ({len(DB_METADATA)} элементов)",
            dependencies=["languages"],
        )

    def should_run(self) -> bool:
        """Проверить, есть ли уже db-концепты"""
        return self.db.query(ConceptModel).filter(ConceptModel.path.like("db/%")).first() is None

    def seed(self) -> None:
        """Создать метаданные БД"""

        # Получаем языки
        languages = {lang.code: lang for lang in self.db.query(LanguageModel).all()}

        required_langs = ["en", "ru"]
        missing_langs = [lang for lang in required_langs if lang not in languages]
        if missing_langs:
            self.logger.warning(f"Missing languages: {missing_langs}")

        # Генерируем все пути
        def generate_all_paths(metadata_paths):
            all_paths = set()
            for path in metadata_paths:
                parts = path.split('/')
                for i in range(1, len(parts) + 1):
                    all_paths.add('/'.join(parts[:i]))
            return all_paths

        all_paths = generate_all_paths(DB_METADATA.keys())
        self.logger.info(f"Generated {len(all_paths)} total paths for DB metadata")

        # Сортируем по глубине
        paths_by_depth = {}
        for path in all_paths:
            depth = path.count("/")
            if depth not in paths_by_depth:
                paths_by_depth[depth] = []
            paths_by_depth[depth].append(path)

        # Создаем концепты
        path_to_id = {}
        total_concepts = 0

        for depth in sorted(paths_by_depth.keys()):
            concepts_data = []

            for path in paths_by_depth[depth]:
                parent_id = None
                if "/" in path:
                    parent_path = path.rsplit("/", 1)[0]
                    parent_id = path_to_id.get(parent_path)

                concepts_data.append({"path": path, "depth": depth, "parent_id": parent_id})

            if concepts_data:
                created = self.batch_insert(ConceptModel, concepts_data, batch_size=100)
                self.db.flush()

                for concept_data in concepts_data:
                    concept = (
                        self.db.query(ConceptModel)
                        .filter_by(path=concept_data["path"])
                        .first()
                    )
                    if concept:
                        path_to_id[concept.path] = concept.id

                total_concepts += created

        self.db.commit()
        self.metadata.records_created = total_concepts

        # Создаем переводы
        dictionaries_data = []

        for path in all_paths:
            concept_id = path_to_id.get(path)
            if not concept_id:
                continue

            if path in DB_METADATA:
                translations = DB_METADATA[path]
                for lang_code, translation_text in translations.items():
                    if lang_code in languages:
                        dictionaries_data.append(
                            {
                                "concept_id": concept_id,
                                "language_id": languages[lang_code].id,
                                "name": translation_text,
                                "description": f"Database metadata for {path}",
                            }
                        )
            else:
                # Промежуточный путь
                path_name = path.split('/')[-1].replace('_', ' ').title()
                for lang_code in required_langs:
                    if lang_code in languages:
                        dictionaries_data.append(
                            {
                                "concept_id": concept_id,
                                "language_id": languages[lang_code].id,
                                "name": path_name,
                                "description": f"Container for {path}",
                            }
                        )

        if dictionaries_data:
            translations_created = self.batch_insert(
                DictionaryModel, dictionaries_data, batch_size=500
            )
            self.db.commit()
            self.metadata.records_created += translations_created
            self.logger.info(f"Created {translations_created} translations")

        self.logger.info(
            f"Total: {total_concepts} concepts with {translations_created} translations"
        )
