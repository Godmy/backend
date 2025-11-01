---
id: F011
title: Two-Factor Authentication (2FA)
type: feature
state: new
priority: 80
effort: M
story_points: 8
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [security, 2fa, auth, totp]
ai_summary: >
  Внедрить двухфакторную аутентификацию (2FA) на основе TOTP (Google
  Authenticator), включая генерацию QR-кодов и резервные коды.
---

### #11 - Two-Factor Authentication (2FA)

**User Story:**
Как пользователь, я хочу включить 2FA, чтобы повысить безопасность аккаунта.

**Acceptance Criteria:**
- [ ] TOTP-based 2FA (Google Authenticator)
- [ ] QR code generation при setup
- [ ] Backup codes для recovery
- [ ] Optional 2FA (пользователь выбирает)
- [ ] GraphQL mutations: enable2FA, verify2FA, disable2FA

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog