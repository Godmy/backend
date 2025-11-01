---
id: T036
title: Load Testing Framework
type: task
state: new
priority: 75
effort: M
story_points: 8
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [performance, load-testing, locust, k6, ci-cd]
ai_summary: >
  Внедрить фреймворк для нагрузочного тестирования (Locust или k6)
  для проверки масштабируемости API и интеграции тестов производительности
  в CI/CD.
---

### #36 - Load Testing Framework

**User Story:**
Как performance engineer, я хочу framework для load testing, чтобы проверить масштабируемость.

**Acceptance Criteria:**
- [ ] Locust или k6 для load testing
- [ ] Test scenarios: login, search, CRUD operations
- [ ] Target: 1000 RPS, p95 latency <200ms
- [ ] CI/CD integration (performance regression tests)
- [ ] Reports: throughput, latency percentiles, errors

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog