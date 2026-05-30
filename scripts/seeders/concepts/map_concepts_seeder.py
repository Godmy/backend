"""
Сидер для карты сайта (site map / routes)
Создаёт структуру доступных страниц с их роутами для Svelte
"""

import logging

from languages.models import ConceptModel, DictionaryModel, LanguageModel
from scripts.seeders.base import BaseSeeder, SeederMetadata, registry

logger = logging.getLogger(__name__)

# Карта сайта с роутами
SITE_MAP = {
    "map/pages/home": {
        "route": "/",
        "en": {"name": "Home", "description": "Home page"},
        "ru": {"name": "Главная", "description": "Главная страница"},
    },
    "map/pages/about": {
        "route": "/about",
        "en": {"name": "About Us", "description": "About our company"},
        "ru": {"name": "О нас", "description": "О нашей компании"},
    },
    "map/pages/services": {
        "route": "/services",
        "en": {"name": "Services", "description": "Our services"},
        "ru": {"name": "Услуги", "description": "Наши услуги"},
    },
    "map/pages/services/consulting": {
        "route": "/services/consulting",
        "en": {"name": "Consulting", "description": "Business consulting services"},
        "ru": {"name": "Консалтинг", "description": "Услуги бизнес-консалтинга"},
    },
    "map/pages/services/development": {
        "route": "/services/development",
        "en": {"name": "Development", "description": "Software development services"},
        "ru": {"name": "Разработка", "description": "Услуги разработки ПО"},
    },
    "map/pages/contact": {
        "route": "/contact",
        "en": {"name": "Contact", "description": "Contact us"},
        "ru": {"name": "Контакты", "description": "Свяжитесь с нами"},
    },
    "map/admin/dashboard": {
        "route": "/admin",
        "en": {"name": "Admin Dashboard", "description": "Administration panel"},
        "ru": {"name": "Админ-панель", "description": "Панель администрирования"},
    },
    "map/admin/users": {
        "route": "/admin/users",
        "en": {"name": "User Management", "description": "Manage users"},
        "ru": {"name": "Управление пользователями", "description": "Управление пользователями"},
    },
    "map/admin/concepts": {
        "route": "/admin/concepts",
        "en": {"name": "Concept Management", "description": "Manage concepts"},
        "ru": {"name": "Управление концептами", "description": "Управление концептами"},
    },
}


@registry.register("map_concepts")
class MapConceptsSeeder(BaseSeeder):
    """Создание карты сайта (routes)"""

    @property
    def metadata(self) -> SeederMetadata:
        return SeederMetadata(
            name="map_concepts",
            version="1.0.0",
            description=f"Создание карты сайта ({len(SITE_MAP)} страниц)",
            dependencies=["languages"],
        )

    def should_run(self) -> bool:
        """Проверить, есть ли уже map-концепты"""
        return self.db.query(ConceptModel).filter(ConceptModel.path.like("map/%")).first() is None

    def seed(self) -> None:
        """Создать карту сайта с роутами"""

        # Получаем языки
        languages = {lang.code: lang for lang in self.db.query(LanguageModel).all()}

        required_langs = ["en", "ru"]
        missing_langs = [lang for lang in required_langs if lang not in languages]
        if missing_langs:
            self.logger.warning(f"Missing languages: {missing_langs}")

        # Генерируем все пути (включая промежуточные)
        def generate_all_paths(site_map_paths):
            """Генерирует все промежуточные пути"""
            all_paths = set()
            for path in site_map_paths:
                parts = path.split('/')
                for i in range(1, len(parts) + 1):
                    all_paths.add('/'.join(parts[:i]))
            return all_paths

        all_paths = generate_all_paths(SITE_MAP.keys())
        self.logger.info(f"Generated {len(all_paths)} total paths for site map")

        # Сортируем по глубине
        paths_by_depth = {}
        for path in all_paths:
            depth = path.count("/")
            if depth not in paths_by_depth:
                paths_by_depth[depth] = []
            paths_by_depth[depth].append(path)

        # Создаем концепты уровень за уровнем
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
                self.logger.info(f"Created {created} concepts at depth {depth}")

        self.db.commit()
        self.metadata.records_created = total_concepts

        # Создаем переводы
        dictionaries_data = []

        for path in all_paths:
            concept_id = path_to_id.get(path)
            if not concept_id:
                continue

            # Если есть данные в SITE_MAP
            if path in SITE_MAP:
                site_data = SITE_MAP[path]
                route = site_data.get("route", "")

                for lang_code in required_langs:
                    if lang_code in languages and lang_code in site_data:
                        lang_data = site_data[lang_code]
                        dictionaries_data.append(
                            {
                                "concept_id": concept_id,
                                "language_id": languages[lang_code].id,
                                "name": lang_data["name"],
                                "description": f"{route} | {lang_data['description']}",
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
