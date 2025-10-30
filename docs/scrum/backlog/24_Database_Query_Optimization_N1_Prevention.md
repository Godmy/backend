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