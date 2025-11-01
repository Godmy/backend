---
id: T023
title: Input Validation & Sanitization Middleware
type: task
state: new
priority: 85
effort: M
story_points: 8
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [security, validation, sanitization, xss, middleware]
ai_summary: >
  Создать middleware для валидации и санации всех входных данных
  для предотвращения XSS и инъекций, с логированием отклоненных запросов.
---

### #23 - Input Validation & Sanitization Middleware

**User Story:**
Как администратор безопасности, я хочу валидировать и санитизировать все входные данные, чтобы предотвратить XSS и injection attacks.

**Acceptance Criteria:**
- [ ] Middleware для валидации всех inputs
- [ ] XSS protection (sanitize HTML)
- [ ] SQL injection prevention (через ORM)
- [ ] Validate GraphQL inputs (types, ranges, lengths)
- [ ] Reject requests с подозрительными паттернами
- [ ] Logging всех rejected requests

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog