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