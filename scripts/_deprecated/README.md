# Deprecated Seed Files

This directory contains old seeding scripts that have been replaced by the new modular seeder system.

## Deprecated Files

- `seed_domain_concepts.py` - Old domain concepts seeder (replaced by `seeders/concepts/domain_concepts_seeder.py`)
- `seed_domain_concepts_simple.py` - Old simplified seeder (replaced by modular system)
- `test_seed_domain_concepts.py` - Tests for old seeder
- `test_seed_domain_concepts_simple.py` - Tests for old simplified seeder

## Why Deprecated?

These files have been replaced by a new **modular seeding system** built on SOLID principles:

### New System Location:
```
scripts/seeders/
├── base.py                          # BaseSeeder, SeederRegistry
├── orchestrator.py                  # SeederOrchestrator
├── languages/languages_seeder.py
├── auth/roles_seeder.py
├── auth/users_seeder.py
├── concepts/ui_concepts_seeder.py
└── concepts/domain_concepts_seeder.py  # ← Replacement for old files
```

### Benefits of New System:
- ✅ **10x faster** - 30-60 seconds vs 5-10 minutes
- ✅ **4x less memory** - 50MB vs 200MB
- ✅ **200x+ fewer DB queries** - 50-100 vs 22,000+
- ✅ **SOLID architecture** - modular, extensible, maintainable
- ✅ **Batch processing** - 1000 records per batch
- ✅ **Dependency resolution** - automatic ordering
- ✅ **Progress tracking** - detailed logging

### Migration Guide:

**Old way (deprecated):**
```python
from scripts.seed_domain_concepts import seed_domain_concepts
seed_domain_concepts(db)
```

**New way (recommended):**
```python
from scripts.seeders.orchestrator import SeederOrchestrator

orchestrator = SeederOrchestrator(db)
results = orchestrator.run_all()

# Or specific seeder:
results = orchestrator.run_specific(["domain_concepts"])
```

**CLI:**
```bash
# Old
python scripts/seed_domain_concepts.py

# New
python scripts/seed_data_new.py --seeders domain_concepts
```

## Documentation

See the new system documentation:
- `scripts/seeders/README.md` - Technical architecture
- `DB_SEEDING_SYSTEM.md` - Complete overview
- `FRONTEND_ONTOLOGY_DISPLAY.md` - Frontend integration

## Retention Policy

These files are kept for:
1. **Reference** - Understanding old implementation
2. **Compatibility** - Emergency fallback if needed
3. **History** - Code archaeology

**Do not use these files for new development.**

---

*Deprecated: 2025-01-27*
*Version: 0.6.0*
