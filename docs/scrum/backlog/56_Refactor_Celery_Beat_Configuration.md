---
id: T056
title: Refactor Celery Beat Configuration
type: task
state: new
priority: 60
effort: S
story_points: 3
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [refactoring, celery, config, devops]
ai_summary: >
  Провести рефакторинг конфигурации Celery Beat, объединив все
  расписания периодических задач в один файл для упрощения управления.
---

### #56 - Refactor Celery Beat Configuration

**User Story:**
Как разработчик, я хочу иметь единую конфигурацию для всех периодических задач (Celery Beat), чтобы избежать путаницы и упростить управление расписанием.

**Acceptance Criteria:**
- [ ] Объединить все `beat_schedule` в одном файле (например, `core/celery_app.py`).
- [ ] Удалить дублирующую конфигурацию из `tasks/periodic_tasks.py`.
- [ ] Убедиться, что все периодические задачи (очистка, бэкапы, health checks) по-прежнему работают корректно.
- [ ] Обновить документацию, если необходимо, чтобы отразить новое местоположение конфигурации.

**Estimated Effort:** 3 story points

**Status:** 📋 Backlog