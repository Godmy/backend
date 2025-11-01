---
id: F031
title: WebSocket Support для Real-time Updates
type: feature
state: new
priority: 80
effort: L
story_points: 13
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [websockets, real-time, pub-sub, redis]
ai_summary: >
  Добавить поддержку WebSocket для обновлений в реальном времени,
  используя Redis pub/sub для широковещательной рассылки событий.
---

### #31 - WebSocket Support для Real-time Updates

**User Story:**
Как пользователь, я хочу WebSocket соединение для real-time обновлений, чтобы не делать polling.

**Acceptance Criteria:**
- [ ] WebSocket endpoint: /ws
- [ ] Authentication через JWT token
- [ ] Events: concept.updated, user.online, notification.new
- [ ] Redis pub/sub для broadcast в multi-instance setup
- [ ] Graceful reconnection на клиенте

**Estimated Effort:** 13 story points

**Status:** 📋 Backlog