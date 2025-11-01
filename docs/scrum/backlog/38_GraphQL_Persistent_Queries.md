---
id: T038
title: GraphQL Persistent Queries
type: task
state: new
priority: 70
effort: S
story_points: 5
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [graphql, performance, security, persistent-queries]
ai_summary: >
  Внедрить поддержку персистентных GraphQL-запросов для уменьшения
  размера трафика и повышения безопасности за счет выполнения только
  заранее зарегистрированных запросов.
---

### #38 - GraphQL Persistent Queries

**User Story:**
Как разработчик, я хочу использовать persistent queries, чтобы снизить размер запросов и повысить безопасность.

**Acceptance Criteria:**
- [ ] Registry для pre-registered queries
- [ ] Query hash вместо full query в production
- [ ] Automatic query registration process
- [ ] Reject non-whitelisted queries в production
- [ ] Support для query versioning

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog