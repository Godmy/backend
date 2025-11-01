---
id: T032
title: Enhanced Health Checks
type: task
state: wip
priority: 85
effort: S
story_points: 5
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [health-checks, monitoring, devops, kubernetes]
ai_summary: >
  Реализовать расширенные проверки состояния системы (БД, Redis, Celery)
  с Kubernetes-совместимыми эндпоинтами для надежного мониторинга.
---

### #32 - Enhanced Health Checks

**User Story:**
Как DevOps инженер, я хочу расширенные health checks, чтобы мониторить состояние всех компонентов системы.

**Acceptance Criteria:**
- [ ] Kubernetes-friendly endpoints: `/health/live`, `/health/ready`
- [ ] Проверки: DB, Redis, Celery, disk space, memory
- [ ] Graceful degradation (partial outage reporting)
- [ ] Metrics для response time каждой проверки
- [ ] Configurable timeout для health checks

**Estimated Effort:** 5 story points

**Status:** 🚧 In Progress (basic health checks готовы)