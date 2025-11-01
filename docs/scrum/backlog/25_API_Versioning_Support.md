---
id: T025
title: API Versioning Support
type: task
state: new
priority: 70
effort: M
story_points: 8
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [api, versioning, backward-compatibility]
ai_summary: >
  Реализовать поддержку версионирования API (v1, v2 в URL или header)
  для обеспечения обратной совместимости и управления жизненным циклом API.
---

### #25 - API Versioning Support

**User Story:**
Как API maintainer, я хочу поддерживать несколько версий API, чтобы обеспечить backward compatibility.

**Acceptance Criteria:**
- [ ] Versioning scheme: v1, v2 (в URL или header)
- [ ] Deprecated fields/queries маркировка
- [ ] Automatic schema documentation для каждой версии
- [ ] Migration guide между версиями
- [ ] Sunset policy для старых версий

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog