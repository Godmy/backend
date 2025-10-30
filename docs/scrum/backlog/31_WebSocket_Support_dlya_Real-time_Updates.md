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