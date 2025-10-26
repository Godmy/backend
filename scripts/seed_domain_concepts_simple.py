"""
Скрипт для инициализации доменных концепций аттракторов человеческого организма
Упрощённая версия без сохранения характеристик (min/max значений)
"""

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


def create_concept_hierarchy(db, node: Dict[str, Any], parent_id: Optional[int] = None, parent_path: str = "") -> int:
    """
    Рекурсивно создать концепцию и всю её иерархию без характеристик
    
    Args:
        db: Сессия базы данных
        node: Узел иерархии
        parent_id: ID родительской концепции
        parent_path: Путь родительской концепции
        
    Returns:
        int: ID созданной концепции
    """
    # Формируем путь текущей концепции
    current_path = f"{parent_path}.{node['id']}" if parent_path else node['id']
    
    # Вычисляем глубину
    depth = current_path.count('.')
    
    # Проверяем, существует ли уже концепция с таким путем
    existing_concept = db.query(ConceptModel).filter_by(path=current_path).first()
    if existing_concept:
        concept_id = existing_concept.id
        logger.debug(f"Concept with path {current_path} already exists (ID: {concept_id})")
    else:
        # Создаем новую концепцию
        concept = ConceptModel(
            path=current_path,
            depth=depth,
            parent_id=parent_id
        )
        db.add(concept)
        db.flush()  # Чтобы получить ID
        concept_id = concept.id
        logger.debug(f"Created concept: {current_path} (ID: {concept_id})")
    
    # Создаем словарные записи для всех поддерживаемых языков
    create_dictionary_entries(db, concept_id, node['name'])
    
    # Рекурсивно обрабатываем дочерние узлы
    for child in node.get('children', []):
        create_concept_hierarchy(db, child, concept_id, current_path)
    
    return concept_id


def create_dictionary_entries(db, concept_id: int, concept_name: str):
    """
    Создать словарные записи для концепции на всех поддерживаемых языках
    
    Args:
        db: Сессия базы данных
        concept_id: ID концепции
        concept_name: Название концепции
    """
    # Получаем все языки
    languages = db.query(LanguageModel).all()
    
    # Для каждого языка создаем словарную запись
    for language in languages:
        # Проверяем, существует ли уже запись для этой концепции и языка
        existing_dict = db.query(DictionaryModel).filter_by(
            concept_id=concept_id,
            language_id=language.id
        ).first()
        
        if not existing_dict:
            # Создаем словарную запись
            dictionary = DictionaryModel(
                concept_id=concept_id,
                language_id=language.id,
                name=concept_name,
                description=""  # Без характеристик
            )
            db.add(dictionary)
            logger.debug(f"Created dictionary entry for {concept_name} in {language.code}")


def seed_domain_concepts_clean(db):
    """
    Основная функция инициализации доменных концепций без характеристик
    
    Args:
        db: Сессия базы данных
    """
    logger.info("=" * 60)
    logger.info("Starting clean domain concepts seeding (without characteristics)...")
    logger.info("=" * 60)
    
    try:
        # Проверяем, есть ли уже доменные концепции (поиск по характерным путям)
        existing = db.query(ConceptModel).filter(ConceptModel.path.like("%.%.%")).first()
        if existing:
            logger.info("Domain concepts already exist, skipping...")
            return
        
        # Загружаем данные онтологии
        root_nodes = load_domain_data()
        
        # Создаем концепции для каждого корневого узла
        total_created = 0
        for root_node in root_nodes:
            concept_id = create_concept_hierarchy(db, root_node)
            total_created += 1
            logger.info(f"Processed root node {root_node['id']} (ID: {concept_id})")
        
        # Коммитим все изменения
        db.commit()
        
        logger.info("=" * 60)
        logger.info("✓ Clean domain concepts seeding completed successfully!")
        logger.info("=" * 60)
        
        # Статистика
        total_concepts = db.query(ConceptModel).count()
        total_dictionaries = db.query(DictionaryModel).count()
        logger.info(f"\nDatabase Statistics:")
        logger.info(f"  Total concepts: {total_concepts}")
        logger.info(f"  Total dictionary entries: {total_dictionaries}")
        logger.info(f"  Languages: {db.query(LanguageModel).count()}")
        
    except Exception as e:
        logger.error(f"Error during clean domain seeding: {e}")
        db.rollback()
        raise


def main():
    """Запуск seed функции для доменных концепций без характеристик"""
    logger.info("=" * 60)
    logger.info("Starting clean domain concepts seeding...")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        seed_domain_concepts_clean(db)
        
        logger.info("=" * 60)
        logger.info("✓ Clean domain concepts seeding completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()