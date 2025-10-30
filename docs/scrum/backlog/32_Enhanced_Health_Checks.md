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