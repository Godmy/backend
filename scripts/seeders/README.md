# Seeder System

The backend uses a modular seeding system driven by:
- `scripts/seed_data.py`
- `scripts/seeders/orchestrator.py`

Current active seeder groups:
- `languages`
- `auth`
- `concepts/ui_concepts_seeder.py`
- `concepts/db_concepts_seeder.py`
- `concepts/map_concepts_seeder.py`

Concept seeding no longer depends on `parser` or `domain_concepts`.
