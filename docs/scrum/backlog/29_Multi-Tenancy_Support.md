---
id: F029
title: Multi-Tenancy Support
type: feature
state: new
priority: 75
effort: XL
story_points: 21
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [multi-tenancy, saas, architecture]
ai_summary: >
  Реализовать поддержку multi-tenancy для изоляции данных разных
  организаций, включая идентификацию тенанта и разграничение доступа
  на уровне запросов.
---

### #29 - Multi-Tenancy Support

**User Story:**
Как SaaS провайдер, я хочу поддержку multi-tenancy, чтобы изолировать данные разных организаций.

**Acceptance Criteria:**
- [ ] Модель Organization/Tenant
- [ ] Tenant-scoped queries (все запросы фильтруются по tenant)
- [ ] Separate database schema per tenant (или shared schema)
- [ ] Tenant identification через subdomain/header
- [ ] Admin panel для управления tenants

**Estimated Effort:** 21 story points

**Status:** 📋 Backlog