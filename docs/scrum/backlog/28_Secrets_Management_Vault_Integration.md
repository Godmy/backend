---
id: T028
title: Secrets Management (Vault Integration)
type: task
state: new
priority: 85
effort: M
story_points: 8
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [security, secrets, vault, devops]
ai_summary: >
  Интегрировать HashiCorp Vault для централизованного и безопасного
  управления секретами (пароли БД, JWT-ключи, API-ключи) с поддержкой
  динамической ротации.
---

### #28 - Secrets Management (Vault Integration)

**User Story:**
Как DevOps инженер, я хочу хранить secrets в HashiCorp Vault, чтобы не держать их в .env файлах.

**Acceptance Criteria:**
- [ ] HashiCorp Vault integration
- [ ] Secrets: DB password, JWT secret, API keys
- [ ] Dynamic secrets rotation
- [ ] Fallback на .env при Vault недоступности
- [ ] Audit log для secret access

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog