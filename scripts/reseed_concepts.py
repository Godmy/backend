"""
Скрипт для пересоздания концептов с новой структурой:
- ui/ (переводы интерфейса)
- map/ (карта сайта с роутами)
- db/ (метаданные БД)
- domain/ (предметная область - будет позже)
"""

import sys
sys.path.insert(0, '.')

from core.platform.db.init_db import import_all_models
import_all_models()

from core.platform.db.database import SessionLocal
from languages.models.concept import ConceptModel
from languages.models.dictionary import DictionaryModel

print('\n' + '='*80)
print('RESEED CONCEPTS WITH NEW STRUCTURE')
print('='*80)

db = SessionLocal()

try:
    # Удаляем все существующие концепты
    print('\n[1/3] Deleting existing concepts...')
    deleted_dicts = db.query(DictionaryModel).delete()
    deleted_concepts = db.query(ConceptModel).delete()
    db.commit()
    print(f'  Deleted {deleted_concepts} concepts and {deleted_dicts} translations')

    # Запускаем сидеры
    print('\n[2/3] Running seeders...')
    from scripts.seed_data import main
    exit_code = main(['--seeders', 'ui_concepts', 'map_concepts', 'db_concepts'])

    if exit_code != 0:
        print(f'  ERROR: Seeding failed with code {exit_code}')
        sys.exit(exit_code)

    # Проверяем результат
    print('\n[3/3] Verifying results...')

    ui_count = db.query(ConceptModel).filter(ConceptModel.path.like('ui%')).count()
    map_count = db.query(ConceptModel).filter(ConceptModel.path.like('map%')).count()
    db_count = db.query(ConceptModel).filter(ConceptModel.path.like('db%')).count()

    print(f'\n  UI concepts: {ui_count}')
    print(f'  MAP concepts: {map_count}')
    print(f'  DB concepts: {db_count}')

    # Проверяем корневые концепты
    root_concepts = db.query(ConceptModel).filter(ConceptModel.depth == 0).all()
    print(f'\n  Root concepts (depth=0): {len(root_concepts)}')
    for c in sorted(root_concepts, key=lambda x: x.path):
        print(f'    - {c.path}')

    print('\n' + '='*80)
    print('SUCCESS! Concepts reseeded with new structure')
    print('='*80)

except Exception as e:
    print(f'\nERROR: {e}')
    import traceback
    traceback.print_exc()
    db.rollback()
    sys.exit(1)
finally:
    db.close()
