---
id: F012
title: Comment System для концепций
type: feature
state: new
priority: 70
effort: M
story_points: 8
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [comments, collaboration, social]
ai_summary: >
  Реализовать систему комментирования для концепций с поддержкой
  вложенности, упоминаний (@username) и форматирования Markdown.
---

### #12 - Comment System для концепций

**User Story:**
Как пользователь, я хочу оставлять комментарии к концепциям, чтобы обсуждать их с другими.

**Acceptance Criteria:**
- [ ] Модель Comment (user, concept, text, parent_id для threads)
- [ ] GraphQL mutations: addComment, editComment, deleteComment
- [ ] Nested comments (до 3 уровней)
- [ ] Mentions (@username)
- [ ] Rich text support (Markdown)

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog