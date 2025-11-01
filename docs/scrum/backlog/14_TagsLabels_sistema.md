---
id: F014
title: Tags/Labels система
type: feature
state: new
priority: 60
effort: S
story_points: 5
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [tags, labels, organization]
ai_summary: >
  Создать систему тегов/меток для организации контента, включая
  возможность добавления, удаления и фильтрации концепций по тегам.
---

### #14 - Tags/Labels система

**User Story:**
Как пользователь, я хочу добавлять теги к концепциям, чтобы организовать контент.

**Acceptance Criteria:**
- [ ] Модель Tag (name, color)
- [ ] Many-to-many: Concept ↔ Tag
- [ ] GraphQL mutations: addTag, removeTag
- [ ] Tag autocomplete/suggestions
- [ ] Filter concepts by tags

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog