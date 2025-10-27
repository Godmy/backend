"""
Сидер для доменных концептов (онтология аттракторов человека)
Зависит от языков

ОПТИМИЗИРОВАН ДЛЯ БОЛЬШИХ ОБЪЕМОВ:
- Batch processing по 1000 записей
- Level-by-level loading (по уровням глубины)
- bulk_insert_mappings вместо add()
- Минимизация запросов к БД
- Прогресс-бары для отслеживания

Загружает ~11000-15000 узлов иерархии из parser/output.json
"""

import json
import logging
import os
from typing import Any, Dict, List

from languages.models import ConceptModel, DictionaryModel, LanguageModel
from scripts.seeders.base import BaseSeeder, SeederMetadata, registry

logger = logging.getLogger(__name__)


@registry.register("domain_concepts")
class DomainConceptsSeeder(BaseSeeder):
    """Создание доменных концептов онтологии человека (оптимизированная версия)"""

    @property
    def metadata(self) -> SeederMetadata:
        return SeederMetadata(
            name="domain_concepts",
            version="1.0.0",
            description="Онтология аттракторов человека (~11000-15000 концептов)",
            dependencies=["languages"],  # Зависит от языков
        )

    def should_run(self) -> bool:
        """Проверить, есть ли уже доменные концепты (с точкой в пути)"""
        # Доменные концепты имеют путь вида "1.", "1.1.", и т.д.
        return self.db.query(ConceptModel).filter(ConceptModel.path.like("%.%")).first() is None

    def load_ontology_data(self) -> List[Dict[str, Any]]:
        """
        Загрузить данные онтологии из parser/output.json

        Returns:
            Список корневых узлов иерархии
        """
        # Определяем путь к файлу парсера
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        parser_file = os.path.join(project_root, "parser", "output.json")

        self.logger.info(f"Loading ontology from: {parser_file}")

        if not os.path.exists(parser_file):
            raise FileNotFoundError(f"Ontology file not found: {parser_file}")

        with open(parser_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data if isinstance(data, list) else [data]

    def flatten_hierarchy(
        self, node: Dict[str, Any], parent_path: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Преобразовать иерархию в плоский список узлов

        Args:
            node: Узел иерархии
            parent_path: Путь к родителю

        Returns:
            Плоский список всех узлов
        """
        nodes = []

        # Формируем путь текущего узла
        node_id = node["id"]
        current_path = f"{parent_path}.{node_id}" if parent_path else node_id

        # Добавляем текущий узел
        flat_node = {
            "id": node_id,
            "path": current_path,
            "name": node["name"],
            "characteristic": node.get("characteristic"),
            "parent_path": parent_path if parent_path else None,
        }
        nodes.append(flat_node)

        # Рекурсивно обрабатываем дочерние узлы
        for child in node.get("children", []):
            nodes.extend(self.flatten_hierarchy(child, current_path))

        return nodes

    def seed(self) -> None:
        """
        Основная логика с оптимизациями:
        1. Загрузка и преобразование иерархии
        2. Batch insert концептов по уровням глубины
        3. Batch insert словарных записей
        """

        # === ЭТАП 1: Загрузка и преобразование данных ===
        self.logger.info("=" * 60)
        self.logger.info("STAGE 1: Loading and flattening ontology hierarchy")
        self.logger.info("=" * 60)

        root_nodes = self.load_ontology_data()
        self.logger.info(f"Loaded {len(root_nodes)} root nodes")

        # Преобразуем иерархию в плоский список
        flat_nodes = []
        for root_node in root_nodes:
            flat_nodes.extend(self.flatten_hierarchy(root_node))

        total_nodes = len(flat_nodes)
        self.logger.info(f"Flattened to {total_nodes} total nodes")

        # === ЭТАП 2: Создание концептов level-by-level ===
        self.logger.info("=" * 60)
        self.logger.info("STAGE 2: Creating concepts (level-by-level)")
        self.logger.info("=" * 60)

        # Группируем узлы по уровню глубины (количество точек)
        nodes_by_depth = {}
        for node in flat_nodes:
            depth = node["path"].count(".")
            if depth not in nodes_by_depth:
                nodes_by_depth[depth] = []
            nodes_by_depth[depth].append(node)

        max_depth = max(nodes_by_depth.keys())
        self.logger.info(f"Max depth: {max_depth}")

        # Мапинг path -> concept_id для быстрого поиска
        path_to_id = {}
        total_concepts_created = 0

        # Создаем концепты уровень за уровнем
        for depth in sorted(nodes_by_depth.keys()):
            depth_nodes = nodes_by_depth[depth]
            self.logger.info(f"\nProcessing depth {depth}: {len(depth_nodes)} nodes")

            # Подготавливаем данные для batch insert
            concepts_data = []
            for node in depth_nodes:
                # Находим parent_id
                parent_id = None
                if node["parent_path"]:
                    parent_id = path_to_id.get(node["parent_path"])

                concepts_data.append(
                    {
                        "path": node["path"],
                        "depth": depth,
                        "parent_id": parent_id,
                    }
                )

            # Batch insert концептов
            created = self.batch_insert(ConceptModel, concepts_data, batch_size=1000)
            self.db.flush()

            # Получаем ID созданных концептов и обновляем мапинг
            # Используем один запрос для всех путей этого уровня
            paths = [node["path"] for node in depth_nodes]
            concepts = self.db.query(ConceptModel).filter(ConceptModel.path.in_(paths)).all()

            for concept in concepts:
                path_to_id[concept.path] = concept.id

            total_concepts_created += created
            self.logger.info(f"✓ Depth {depth}: created {created} concepts")

        # Commit всех концептов
        self.db.commit()
        self.metadata.records_created = total_concepts_created
        self.logger.info(f"\n✓ Total concepts created: {total_concepts_created}")

        # === ЭТАП 3: Создание словарных записей ===
        self.logger.info("=" * 60)
        self.logger.info("STAGE 3: Creating dictionary entries")
        self.logger.info("=" * 60)

        # Получаем все языки
        languages = {lang.code: lang for lang in self.db.query(LanguageModel).all()}
        self.logger.info(f"Found {len(languages)} languages: {list(languages.keys())}")

        # Подготавливаем словарные записи для batch insert
        dictionaries_data = []

        for node in flat_nodes:
            concept_id = path_to_id.get(node["path"])
            if not concept_id:
                self.logger.warning(f"Concept not found for path: {node['path']}")
                continue

            # Создаем запись для каждого языка
            # Пока используем русский как основной (можно расширить позже)
            for lang_code, language in languages.items():
                # Формируем описание с характеристиками (если есть)
                description = None
                if node.get("characteristic"):
                    description = json.dumps(node["characteristic"], ensure_ascii=False)

                dictionaries_data.append(
                    {
                        "concept_id": concept_id,
                        "language_id": language.id,
                        "name": node["name"],
                        "description": description,
                    }
                )

        # Batch insert словарей
        if dictionaries_data:
            translations_created = self.batch_insert(
                DictionaryModel, dictionaries_data, batch_size=1000
            )
            self.db.commit()
            self.metadata.records_created += translations_created
            self.logger.info(f"✓ Created {translations_created} dictionary entries")

        # === ФИНАЛ: Статистика ===
        self.logger.info("=" * 60)
        self.logger.info("SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Concepts created: {total_concepts_created}")
        self.logger.info(f"Dictionary entries: {translations_created}")
        self.logger.info(f"Languages: {len(languages)}")
        self.logger.info(f"Max depth: {max_depth}")
        self.logger.info(f"Total records: {self.metadata.records_created}")
