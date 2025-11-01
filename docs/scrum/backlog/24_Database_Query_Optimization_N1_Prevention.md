---
id: T024
title: Database Query Optimization & N+1 Prevention
type: task
state: new
priority: 80
effort: M
story_points: 8
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [performance, database, n+1, optimization, dataloader]
ai_summary: >
  Оптимизировать запросы к базе данных для предотвращения проблемы N+1,
  используя SQLAlchemy eager loading (joinedload/subqueryload) и
  интеграцию с GraphQL DataLoader.
---

### #24 - Database Query Optimization & N+1 Prevention

**User Story:**
Как разработчик, я хочу автоматически оптимизировать DB queries, чтобы избежать N+1 проблемы.

**Acceptance Criteria:**
- [ ] SQLAlchemy relationship lazy loading review
- [ ] Добавить joinedload/subqueryload где нужно
- [ ] Query logging в DEBUG mode
- [ ] Monitoring slow queries (>100ms)
- [ ] Indexes для часто используемых полей
- [ ] Database query profiling tools
- [ ] GraphQL DataLoader integration

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog