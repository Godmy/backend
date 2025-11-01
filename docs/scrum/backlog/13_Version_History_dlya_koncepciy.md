---
id: F013
title: Version History для концепций
type: feature
state: new
priority: 70
effort: M
story_points: 8
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [versioning, history, audit]
ai_summary: >
  Реализовать историю версий для концепций, позволяющую просматривать
  изменения, сравнивать версии и восстанавливать предыдущие состояния.
---

### #13 - Version History для концепций

**User Story:**
Как пользователь, я хочу видеть историю изменений концепции, чтобы откатиться к предыдущей версии.

**Acceptance Criteria:**
- [ ] Модель ConceptVersion (snapshot при каждом update)
- [ ] GraphQL query: conceptVersions(conceptId: Int!)
- [ ] Diff между версиями
- [ ] Restore previous version
- [ ] Blame (кто и когда изменил)

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog