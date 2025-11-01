---
id: T051
title: Docker Multi-Stage Build Optimization
type: task
state: new
priority: 70
effort: S
story_points: 5
created: 2025-11-01
updated: 2025-11-01
owner: backend-team
tags: [docker, optimization, ci-cd, devops]
ai_summary: >
  Оптимизировать Docker-сборку с использованием multi-stage builds для
  уменьшения размера итогового образа (<200MB) и ускорения развертывания.
---

### #51 - Docker Multi-Stage Build Optimization

**User Story:**
Как DevOps инженер, я хочу оптимизировать Docker build, чтобы ускорить deployment и снизить image size.

**Acceptance Criteria:**
- [ ] Multi-stage Dockerfile
- [ ] Build dependencies в separate stage
- [ ] Image size <200MB (сейчас ~500MB)
- [ ] Layer caching optimization
- [ ] .dockerignore для исключения лишних файлов
- [ ] Security scanning (Trivy/Grype)

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog