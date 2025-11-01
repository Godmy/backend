---
id: T034
title: Data Migration Tools
type: task
state: new
priority: 75
effort: M
story_points: 8
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [data-migration, cli, database]
ai_summary: >
  Создать CLI-инструменты для миграции данных между окружениями,
  включая выборочный экспорт, трансформацию и механизм отката.
---

### #34 - Data Migration Tools

**User Story:**
Как администратор данных, я хочу инструменты для миграции данных между окружениями, чтобы безопасно переносить данные.

**Acceptance Criteria:**
- [ ] CLI commands для dump/restore данных
- [ ] Selective export (по entities, dates, filters)
- [ ] Data transformation при миграции
- [ ] Dry-run mode для проверки
- [ ] Rollback mechanism
- [ ] Progress reporting для больших datasets

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog