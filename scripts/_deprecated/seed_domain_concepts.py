"""
Скрипт для инициализации доменных концепций аттракторов человеческого организма
Импортирует иерархическую онтологию из parser/output.json
"""

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

from core.database import SessionLocal
from languages.models import ConceptModel, DictionaryModel, LanguageModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_domain_data(parser_output_path: str = "parser/output.json") -> List[Dict[str, Any]]:
    """
    Загрузить данные онтологии из файла парсера
    
    Args:
        parser_output_path: Путь к файлу output.json
        
    Returns:
        List[Dict]: Список корневых узлов онтологии
    """
    # Определяем абсолютный путь к файлу
    if not os.path.isabs(parser_output_path):
        # Если путь относительный, строим его от корня проекта
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        parser_output_path = os.path.join(project_root, parser_output_path)
    
    logger.info(f"Loading domain data from: {parser_output_path}")
    
    if not os.path.exists(parser_output_path):
        raise FileNotFoundError(f"Parser output file not found: {parser_output_path}")
    
    with open(parser_output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data) if isinstance(data, list) else 1} root nodes")
    return data if isinstance(data, list) else [data]


def flatten_hierarchy(node: Dict[str, Any], parent_path: str = "") -> List[Dict[str, Any]]:
    """
    Преобразовать иерархию в плоский список узлов
    
    Args:
        node: Узел иерархии
        parent_path: Путь к родительскому узлу
        
    Returns:
        List[Dict]: Плоский список всех узлов
    """
    nodes = []
    
    # Формируем путь текущего узла
    current_path = f"{parent_path}.{node['id']}" if parent_path else node['id']
    
    # Добавляем текущий узел
    flat_node = {
        'id': node['id'],
        'path': current_path,
        'name': node['name'],
        'characteristic': node.get('characteristic'),
        'parent_path': parent_path if parent_path else None
    }
    nodes.append(flat_node)
    
    # Рекурсивно обрабатываем дочерние узлы
    for child in node.get('children', []):
        nodes.extend(flatten_hierarchy(child, current_path))
    
    return nodes


def get_or_create_concept(db, flat_nodes: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Получить или создать концепции из плоского списка
    
    Args:
        db: Сессия базы данных
        flat_nodes: Плоский список узлов
        
    Returns:
        Dict[str, int]: Словарь path -> concept_id
    """
    # Создаем словарь для быстрого поиска узлов по пути
    node_dict = {node['path']: node for node in flat_nodes}
    
    # Получаем все существующие концепции
    existing_concepts = db.query(ConceptModel).filter(
        ConceptModel.path.in_([node['path'] for node in flat_nodes])
    ).all()
    
    # Создаем словарь существующих концепций path -> concept
    existing_dict = {concept.path: concept for concept in existing_concepts}
    
    # Определяем, какие концепции нужно создать
    concepts_to_create = []
    path_to_id_map = {}
    
    # Сначала добавляем существующие концепции в карту
    for path, concept in existing_dict.items():
        path_to_id_map[path] = concept.id
    
    # Затем создаем новые концепции
    concepts_created = 0
    for node in flat_nodes:
        path = node['path']
        if path not in path_to_id_map:
            # Определяем parent_id
            parent_path = node['parent_path']
            parent_id = path_to_id_map.get(parent_path) if parent_path else None
            
            # Вычисляем глубину
            depth = path.count('.')  # Количество точек в пути
            
            # Создаем новую концепцию
            concept = ConceptModel(
                path=path,
                depth=depth,
                parent_id=parent_id
            )
            db.add(concept)
            concepts_to_create.append((concept, node))
    
    # Флешим, чтобы получить ID для новых концепций
    if concepts_to_create:
        db.flush()
        
        # Обновляем карту с новыми концепциями
        for concept, node in concepts_to_create:
            path_to_id_map[node['path']] = concept.id
            concepts_created += 1
    
    logger.info(f"Processed {len(flat_nodes)} concepts, created {concepts_created} new concepts")
    return path_to_id_map


def create_dictionary_entries(db, path_to_id_map: Dict[str, int], flat_nodes: List[Dict[str, Any]]):
    """
    Создать словарные записи для концепций
    
    Args:
        db: Сессия базы данных
        path_to_id_map: Словарь path -> concept_id
        flat_nodes: Плоский список узлов
    """
    # Получаем все языки
    languages = {lang.code: lang for lang in db.query(LanguageModel).all()}
    logger.info(f"Found {len(languages)} supported languages: {list(languages.keys())}")
    
    # Проверяем существующие словарные записи
    concept_ids = list(path_to_id_map.values())
    existing_dicts = db.query(DictionaryModel).filter(
        DictionaryModel.concept_id.in_(concept_ids)
    ).all()
    
    # Создаем множество существующих пар (concept_id, language_id)
    existing_pairs = {(d.concept_id, d.language_id) for d in existing_dicts}
    
    # Создаем словарные записи
    dictionaries_to_create = []
    
    for node in flat_nodes:
        path = node['path']
        concept_id = path_to_id_map.get(path)
        
        if not concept_id:
            continue
            
        # Для каждого языка создаем словарную запись
        for lang_code, language in languages.items():
            # Проверяем, существует ли уже такая запись
            if (concept_id, language.id) in existing_pairs:
                continue
                
            # Формируем описание с характеристиками
            description_parts = [node['name']]
            if node.get('characteristic'):
                char = node['characteristic']
                if char.get('min') is not None and char.get('max') is not None:
                    description_parts.append(f"({char['min']}-{char['max']})")
            
            description = " ".join(description_parts) if len(description_parts) > 1 else ""
            
            # Создаем словарную запись
            dictionary = DictionaryModel(
                concept_id=concept_id,
                language_id=language.id,
                name=node['name'],
                description=json.dumps(node['characteristic']) if node.get('characteristic') else None
            )
            db.add(dictionary)
            dictionaries_to_create.append(dictionary)
            
            # Добавляем в существующие пары, чтобы избежать дубликатов
            existing_pairs.add((concept_id, language.id))
    
    db.commit()
    logger.info(f"Created {len(dictionaries_to_create)} dictionary entries")


def seed_domain_concepts(db):
    """
    Основная функция инициализации доменных концепций
    
    Args:
        db: Сессия базы данных
    """
    logger.info("=" * 60)
    logger.info("Starting domain concepts seeding...")
    logger.info("=" * 60)
    
    try:
        # Проверяем, есть ли уже доменные концепции
        existing = db.query(ConceptModel).filter(ConceptModel.path.like("%.%.%")).first()
        if existing:
            logger.info("Domain concepts already exist, skipping...")
            return
        
        # Загружаем данные онтологии
        root_nodes = load_domain_data()
        
        # Преобразуем иерархию в плоский список
        logger.info("Flattening hierarchy...")
        flat_nodes = []
        for root_node in root_nodes:
            flat_nodes.extend(flatten_hierarchy(root_node))
        
        logger.info(f"Flattened to {len(flat_nodes)} nodes")
        
        # Получаем или создаем концепции
        logger.info("Processing concepts...")
        path_to_id_map = get_or_create_concept(db, flat_nodes)
        
        # Создаем словарные записи
        logger.info("Creating dictionary entries...")
        create_dictionary_entries(db, path_to_id_map, flat_nodes)
        
        logger.info("=" * 60)
        logger.info("✓ Domain concepts seeding completed successfully!")
        logger.info("=" * 60)
        
        # Статистика
        total_concepts = db.query(ConceptModel).count()
        total_dictionaries = db.query(DictionaryModel).count()
        logger.info(f"\nDatabase Statistics:")
        logger.info(f"  Total concepts: {total_concepts}")
        logger.info(f"  Total dictionary entries: {total_dictionaries}")
        
    except Exception as e:
        logger.error(f"Error during domain seeding: {e}")
        db.rollback()
        raise


def main():
    """Запуск seed функции для доменных концепций"""
    logger.info("=" * 60)
    logger.info("Starting domain concepts seeding...")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        seed_domain_concepts(db)
        
        logger.info("=" * 60)
        logger.info("✓ Domain concepts seeding completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()