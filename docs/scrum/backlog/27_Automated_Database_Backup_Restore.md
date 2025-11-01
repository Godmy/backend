---
id: T027
title: Automated Database Backup & Restore
type: task
state: new
priority: 90
effort: M
story_points: 8
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [database, backup, restore, disaster-recovery, celery]
ai_summary: >
  Настроить автоматическое ежедневное резервное копирование базы данных
  (в S3 или локально) с политикой хранения и возможностью восстановления
  на определенный момент времени (PITR).
---

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