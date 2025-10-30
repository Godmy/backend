### #27 - Automated Database Backup & Restore

**User Story:**
Как администратор БД, я хочу автоматические backups, чтобы защититься от потери данных.

**Acceptance Criteria:**
- [ ] Daily backups в S3/local storage
- [ ] Retention policy (7 daily, 4 weekly, 12 monthly)
- [ ] Point-in-time recovery
- [ ] Backup verification (restore test)
- [ ] Celery task для scheduled backups
- [ ] CLI command для manual backup/restore

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog