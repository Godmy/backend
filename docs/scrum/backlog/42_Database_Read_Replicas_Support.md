### #42 - Database Read Replicas Support

**User Story:**
Как архитектор системы, я хочу поддержку read replicas, чтобы масштабировать read operations.

**Acceptance Criteria:**
- [ ] Separate DB connection для reads/writes
- [ ] Automatic routing: mutations → primary, queries → replica
- [ ] Replication lag monitoring
- [ ] Fallback на primary при replica failures
- [ ] Config для multiple replicas (load balancing)

**Estimated Effort:** 13 story points

**Status:** 📋 Backlog