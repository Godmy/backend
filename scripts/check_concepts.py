import sys
sys.path.insert(0, '.')

from core.platform.db.init_db import import_all_models
import_all_models()

from core.platform.db.database import SessionLocal
from languages.models.concept import ConceptModel

db = SessionLocal()

print('\n=== CONCEPTS BY DEPTH ===')
depths = {}
for c in db.query(ConceptModel).all():
    depths[c.depth] = depths.get(c.depth, 0) + 1

for d, count in sorted(depths.items()):
    print(f'Depth {d}: {count} concepts')

print('\n=== SAMPLE PATHS BY DEPTH ===')
for depth in sorted(depths.keys()):
    concepts = db.query(ConceptModel).filter(ConceptModel.depth == depth).limit(5).all()
    print(f'\nDepth {depth}:')
    for c in concepts:
        print(f'  {c.path}')

print('\n=== UNIQUE PATH PREFIXES (first level) ===')
prefixes = set()
for c in db.query(ConceptModel).all():
    prefixes.add(c.path.split('/')[0])

for p in sorted(prefixes):
    print(f'  - {p}')

db.close()
