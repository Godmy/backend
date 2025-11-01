---
id: T050
title: Comprehensive Integration Tests
type: task
state: new
priority: 85
effort: L
story_points: 13
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [testing, integration-tests, qa, ci-cd]
ai_summary: >
  Создать полный набор интеграционных тестов для всех GraphQL-операций,
  OAuth, отправки email и загрузки файлов, с интеграцией в CI/CD и
  целевым покрытием кода >80%.
---

### #50 - Comprehensive Integration Tests

**User Story:**
Как QA инженер, я хочу полный набор integration тестов, чтобы быть уверенным в качестве кода.

**Acceptance Criteria:**
- [ ] Integration tests для всех GraphQL mutations/queries
- [ ] Tests для OAuth flows (Google, Telegram)
- [ ] Tests для email sending (с MailPit)
- [ ] Tests для file uploads
- [ ] Tests для rate limiting
- [ ] CI/CD integration (GitHub Actions)
- [ ] Code coverage >80%

**Estimated Effort:** 13 story points

**Status:** 📋 Backlog