---
id: T026
title: GraphQL Query Complexity Analysis
type: task
state: new
priority: 80
effort: M
story_points: 8
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [security, graphql, performance, complexity-analysis]
ai_summary: >
  Внедрить анализ сложности GraphQL-запросов для предотвращения
  ресурсоемких операций, с возможностью отклонения запросов, превышающих
  установленный порог.
---

### #26 - GraphQL Query Complexity Analysis

**User Story:**
Как администратор безопасности, я хочу анализировать сложность GraphQL queries, чтобы предотвратить expensive queries.

**Acceptance Criteria:**
- [ ] Cost calculation для каждого field
- [ ] Reject queries с cost > threshold
- [ ] Configurable complexity limits
- [ ] Whitelist для admin/internal queries
- [ ] Logging expensive queries

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog