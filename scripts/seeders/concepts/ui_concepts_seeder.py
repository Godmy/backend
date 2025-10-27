"""
Сидер для UI-концептов (интерфейсные переводы)
Зависит от языков
Создает около 200+ концептов с переводами для элементов интерфейса
"""

import logging

from languages.models import ConceptModel, DictionaryModel, LanguageModel
from scripts.seeders.base import BaseSeeder, SeederMetadata, registry

logger = logging.getLogger(__name__)

# Minimal UI translations dictionary
# TODO: Add more translations as needed
UI_TRANSLATIONS = {
    "ui": {"en": "User Interface", "ru": "Пользовательский интерфейс", "es": "Interfaz de usuario"},
    "ui/common": {"en": "Common", "ru": "Общее", "es": "Común"},
    "ui/common/buttons": {"en": "Buttons", "ru": "Кнопки", "es": "Botones"},
    "ui/common/buttons/save": {"en": "Save", "ru": "Сохранить", "es": "Guardar"},
    "ui/common/buttons/cancel": {"en": "Cancel", "ru": "Отмена", "es": "Cancelar"},
    "ui/common/buttons/delete": {"en": "Delete", "ru": "Удалить", "es": "Eliminar"},
}


@registry.register("ui_concepts")
class UIConceptsSeeder(BaseSeeder):
    """Создание UI-концептов для интерфейсных переводов"""

    @property
    def metadata(self) -> SeederMetadata:
        return SeederMetadata(
            name="ui_concepts",
            version="1.0.0",
            description=f"Создание UI-концептов и переводов ({len(UI_TRANSLATIONS)} концептов)",
            dependencies=["languages"],  # Зависит от языков
        )

    def should_run(self) -> bool:
        """Проверить, есть ли уже UI-концепты"""
        return self.db.query(ConceptModel).filter(ConceptModel.path.like("ui/%")).first() is None

    def seed(self) -> None:
        """Создать UI-концепты и переводы с batch оптимизацией"""

        # Получаем языки
        languages = {lang.code: lang for lang in self.db.query(LanguageModel).all()}

        # Проверяем наличие необходимых языков
        required_langs = ["en", "ru", "es"]
        missing_langs = [lang for lang in required_langs if lang not in languages]
        if missing_langs:
            self.logger.warning(
                f"Missing languages: {missing_langs}. Some translations will be skipped."
            )

        # Этап 1: Создаем все концепты по уровням глубины для правильного parent_id
        # Сначала сортируем по глубине (количество / в пути)
        paths_by_depth = {}
        for path in UI_TRANSLATIONS.keys():
            depth = path.count("/")
            if depth not in paths_by_depth:
                paths_by_depth[depth] = []
            paths_by_depth[depth].append(path)

        # Создаем мапинг path -> concept_id
        path_to_id = {}
        total_concepts = 0

        # Создаем концепты уровень за уровнем
        for depth in sorted(paths_by_depth.keys()):
            concepts_data = []

            for path in paths_by_depth[depth]:
                # Находим parent_id
                parent_id = None
                if "/" in path:
                    parent_path = path.rsplit("/", 1)[0]
                    parent_id = path_to_id.get(parent_path)

                concepts_data.append({"path": path, "depth": depth, "parent_id": parent_id})

            # Batch insert концептов этого уровня
            if concepts_data:
                created = self.batch_insert(ConceptModel, concepts_data, batch_size=500)
                self.db.flush()

                # Получаем созданные концепты и строим мапинг
                for concept_data in concepts_data:
                    concept = (
                        self.db.query(ConceptModel)
                        .filter_by(path=concept_data["path"])
                        .first()
                    )
                    if concept:
                        path_to_id[concept.path] = concept.id

                total_concepts += created
                self.logger.info(f"Created {created} concepts at depth {depth}")

        # Commit концептов
        self.db.commit()
        self.metadata.records_created = total_concepts

        # Этап 2: Создаем словарные записи (переводы) с batch insert
        dictionaries_data = []

        for path, translations in UI_TRANSLATIONS.items():
            concept_id = path_to_id.get(path)
            if not concept_id:
                self.logger.warning(f"Concept not found for path: {path}")
                continue

            # Создаем перевод для каждого языка
            for lang_code, translation_text in translations.items():
                if lang_code in languages:
                    dictionaries_data.append(
                        {
                            "concept_id": concept_id,
                            "language_id": languages[lang_code].id,
                            "name": translation_text,
                            "description": f"UI translation for {path}",
                        }
                    )

        # Batch insert словарей
        if dictionaries_data:
            translations_created = self.batch_insert(
                DictionaryModel, dictionaries_data, batch_size=1000
            )
            self.db.commit()
            self.metadata.records_created += translations_created
            self.logger.info(f"Created {translations_created} dictionary translations")

        self.logger.info(
            f"Total: {total_concepts} UI concepts with {translations_created} translations"
        )
