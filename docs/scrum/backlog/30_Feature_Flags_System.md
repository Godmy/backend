---
id: F030
title: Feature Flags System
type: feature
state: new
priority: 70
effort: L
story_points: 13
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [feature-flags, ab-testing, devops]
ai_summary: >
  Реализовать систему feature-флагов для динамического включения/выключения
  функционала, проведения A/B тестов и управления таргетингом.
---

### #30 - Feature Flags System

**User Story:**
Как product manager, я хочу включать/выключать features динамически, чтобы проводить A/B тесты.

**Acceptance Criteria:**
- [ ] Модель FeatureFlag (name, enabled, rules)
- [ ] SDK для проверки flags в коде
- [ ] GraphQL queries: isFeatureEnabled(name: String!)
- [ ] Admin UI для управления flags
- [ ] Targeting rules (по user, role, percentage)

**Estimated Effort:** 13 story points

**Status:** 📋 Backlog